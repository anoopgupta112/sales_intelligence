import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Lead, WorkflowRun
from app.services.workflow_service import workflow_service

logger = logging.getLogger("platform.api.whatsapp")
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

async def send_whatsapp_message(to_phone: str, text: str):
    """Asynchronously send a text message using Meta's Cloud API."""
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        logger.warning(
            "WhatsApp API not configured (WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID is missing). "
            "Simulating reply to %s: %s", to_phone, text
        )
        return
    
    url = f"https://graph.facebook.com/v25.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code != 200:
                logger.error("Failed to send WhatsApp message: Status %s, Response %s", resp.status_code, resp.text)
            else:
                logger.info("WhatsApp message successfully sent to %s", to_phone)
        except Exception as e:
            logger.error("Error sending WhatsApp message: %s", e)

async def process_whatsapp_command(from_phone: str, text_body: str, db: AsyncSession):
    """Parse commands and construct the response."""
    text_clean = text_body.strip()
    text_lower = text_clean.lower()
    
    if not text_clean:
        return

    logger.info("Processing WhatsApp command from %s: '%s'", from_phone, text_clean)

    # 1. HELP Command
    if text_lower == "help" or text_lower == "menu":
        reply = (
            "🤖 *AI Sales Assistant*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Hi! Use these commands to manage your lead workflows:\n\n"
            "📋 *Available Commands:*\n"
            "• *help* ─ Show this menu\n"
            "• *list* ─ Show the 5 latest leads\n"
            "• *search <industry>* ─ Discover & research leads (e.g. `search Robotics`)\n"
            "• *status <run_id>* ─ Check status of a workflow run\n"
            "• *lead <lead_id>* ─ Show detailed lead profile\n\n"
            "💡 *Tip:* You can also just type a company name (e.g. `Acme`) to search for its profile instantly!"
        )

    # 2. SEARCH Command
    elif text_lower.startswith("search "):
        industry = text_clean[7:].strip()
        if not industry:
            reply = "⚠️ *Error:* Please specify an industry (e.g. `search Fintech`)."
        else:
            run_id = await workflow_service.start_workflow({"industry": industry})
            reply = (
                f"🚀 *Lead Discovery Started!*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"A new multi-agent workflow has been launched in the background.\n\n"
                f"• *Target Industry:* {industry}\n"
                f"• *Workflow Run ID:* `{run_id}`\n\n"
                f"Type `status {run_id}` to check on its progress."
            )

    # 3. STATUS Command
    elif text_lower.startswith("status "):
        run_id = text_clean[7:].strip()
        if not run_id:
            reply = "⚠️ *Error:* Please specify a workflow run ID (e.g. `status <run_id>`)."
        else:
            stmt = select(WorkflowRun).where(WorkflowRun.id == run_id)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            if not run:
                reply = f"❌ Workflow run `{run_id}` not found."
            else:
                steps_info = ""
                lead_details = ""
                if run.variables:
                    companies = run.variables.get("companies", [])
                    company_names = [c["company_name"] for c in companies if "company_name" in c]
                    steps_info = (
                        f"🏢 *Discovered:* {len(companies)} companies\n"
                        f"📝 *Researched:* {len(run.variables.get('research_reports', []))} reports\n"
                        f"✅ *Qualified Matches:* {len(run.variables.get('qualification_results', []))} leads\n"
                        f"✉️ *Outreach Drafts:* {len(run.variables.get('outreach_drafts', []))} generated\n"
                    )
                    
                    if company_names:
                        lead_stmt = select(Lead).where(Lead.company_name.in_(company_names))
                        lead_res = await db.execute(lead_stmt)
                        leads = lead_res.scalars().all()
                        if leads:
                            lead_details = "\n✨ *Discovered Lead IDs:*\n"
                            for l in leads:
                                score_str = f"({l.score} pts)" if l.score is not None else ""
                                lead_details += f"• *ID {l.id}:* {l.company_name} ─ {l.status.upper()} {score_str}\n"

                error_msg = f"\n⚠️ *Errors:* {run.errors}" if run.errors else ""
                reply = (
                    f"📊 *Workflow Run Status*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"• *ID:* `{run_id}`\n"
                    f"• *Active Node:* `{run.current_step}`\n"
                    f"• *Status:* *{run.status.upper()}*\n\n"
                    f"📈 *Progress Summary:*\n"
                    f"{steps_info}{error_msg}"
                    f"{lead_details}"
                )

    # 4. LEAD Command
    elif text_lower.startswith("lead "):
        lead_id_str = text_clean[5:].strip()
        
        # Smart handling: If user pasted a UUID run_id instead of integer ID
        if len(lead_id_str) > 10 and "-" in lead_id_str:
            stmt = select(WorkflowRun).where(WorkflowRun.id == lead_id_str)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            if run:
                companies = run.variables.get("companies", [])
                company_names = [c["company_name"] for c in companies if "company_name" in c]
                lead_list_str = ""
                if company_names:
                    lead_stmt = select(Lead).where(Lead.company_name.in_(company_names))
                    lead_res = await db.execute(lead_stmt)
                    leads = lead_res.scalars().all()
                    if leads:
                        lead_list_str = "\n".join([f"• *ID {l.id}:* {l.company_name} ({l.status.upper()})" for l in leads])
                
                reply = (
                    f"💡 *Workflow Run ID Detected!*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"`{lead_id_str}` is a workflow run ID, not a single lead ID.\n\n"
                    f"📂 *Leads Discovered in this Run:*\n"
                    f"{lead_list_str or 'None'}\n\n"
                    f"👉 To view details, type `lead <ID>` (e.g. `lead 5`)."
                )
            else:
                reply = f"❌ Workflow run or lead with ID `{lead_id_str}` not found."
        else:
            try:
                lead_id = int(lead_id_str)
                stmt = select(Lead).where(Lead.id == lead_id)
                res = await db.execute(stmt)
                lead = res.scalar_one_or_none()
                if not lead:
                    reply = f"❌ Lead with ID `{lead_id}` not found."
                else:
                    score_str = f"{lead.score}/100" if lead.score is not None else "N/A"
                    reply = (
                        f"💼 *Lead Profile (ID: {lead.id})*\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"• *Company:* {lead.company_name}\n"
                        f"• *Website:* {lead.domain or 'N/A'}\n"
                        f"• *Industry:* {lead.industry or 'N/A'}\n"
                        f"• *Status:* *{lead.status.upper()}*\n"
                        f"• *ICP Score:* *{score_str}*"
                    )
            except ValueError:
                reply = "⚠️ *Error:* Invalid lead ID. Use the format `lead <ID>` (e.g. `lead 1`)."

    # 5. LIST Command
    elif text_lower == "list" or text_lower == "leads":
        stmt = select(Lead).order_by(Lead.id.desc()).limit(5)
        res = await db.execute(stmt)
        leads = res.scalars().all()
        if not leads:
            reply = "📭 No leads discovered yet. Send `search <industry>` to discover some!"
        else:
            lead_lines = []
            for l in leads:
                score_str = f"({l.score} pts)" if l.score is not None else ""
                lead_lines.append(f"🏢 *ID {l.id}:* {l.company_name} ─ {l.status.upper()} {score_str}")
            reply = (
                f"📋 *Latest Discovered Leads*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(lead_lines) +
                f"\n\n💡 *Tip:* Type `lead <ID>` (e.g. `lead 3`) to view full details."
            )

    # 6. Fallback Search by Company Name
    else:
        stmt = select(Lead).where(Lead.company_name.ilike(f"%{text_clean}%")).limit(1)
        res = await db.execute(stmt)
        lead = res.scalar_one_or_none()
        if lead:
            score_str = f"{lead.score}/100" if lead.score is not None else "N/A"
            reply = (
                f"🔍 *Company Lead Found!*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"• *ID:* {lead.id}\n"
                f"• *Company:* {lead.company_name}\n"
                f"• *Website:* {lead.domain or 'N/A'}\n"
                f"• *Industry:* {lead.industry or 'N/A'}\n"
                f"• *Status:* *{lead.status.upper()}*\n"
                f"• *ICP Score:* *{score_str}*\n\n"
                f"💡 *Tip:* Type `lead {lead.id}` to view more details."
            )
        else:
            reply = (
                f"❓ *Unknown Command:* \"{text_clean}\"\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"I didn't understand that instruction.\n\n"
                f"👉 Send *help* to view the menu of supported commands."
            )

    await send_whatsapp_message(from_phone, reply)

@router.get("/webhook")
async def verify_webhook(request: Request):
    """Handle Meta's challenge/verification step."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verified successfully.")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            logger.warning("WhatsApp verification token mismatch: expected '%s', got '%s'", settings.WHATSAPP_VERIFY_TOKEN, token)
            raise HTTPException(status_code=403, detail="Verification token mismatch")
            
    raise HTTPException(status_code=400, detail="Missing verification parameters")

@router.post("/webhook")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive and route incoming WhatsApp messages."""
    payload = await request.json()
    logger.info("Received WhatsApp webhook payload: %s", payload)
    
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            for message in messages:
                from_phone = message.get("from")
                msg_type = message.get("type")
                
                if msg_type == "text" and from_phone:
                    text_body = message.get("text", {}).get("body", "").strip()
                    await process_whatsapp_command(from_phone, text_body, db)
                    
    return {"status": "success"}
