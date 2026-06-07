import logging
import resend
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Notification
from app.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key


async def create_notification(
    db: AsyncSession,
    notification_type: str,
    title: str,
    body: str,
    send_email: bool = False,
) -> Notification:
    """
    Salva uma notificação no banco (para o dashboard) e,
    se send_email=True, dispara o email via Resend.
    """
    notification = Notification(
        type=notification_type,
        title=title,
        body=body,
        read=False,
    )
    db.add(notification)
    await db.flush()

    if send_email:
        await _send_email(title=title, body=body)

    return notification


async def _send_email(title: str, body: str):
    try:
        params: resend.Emails.SendParams = {
            "from": settings.notification_email_from,
            "to": [settings.notification_email_to],
            "subject": f"[ML Research] {title}",
            "html": _build_email_html(title, body),
        }
        response = resend.Emails.send(params)
        logger.info(f"Email enviado: {response['id']}")
    except Exception as exc:
        # Email não crítico — loga o erro mas não interrompe o fluxo
        logger.error(f"Falha ao enviar email de notificação: {exc}")


def _build_email_html(title: str, body: str) -> str:
    body_html = body.replace("\n", "<br>")
    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
      <h2 style="color: #1a1a1a; margin-bottom: 8px;">{title}</h2>
      <div style="color: #555; line-height: 1.6; margin-bottom: 24px;">
        {body_html}
      </div>
      <a href="http://localhost:5173"
         style="display: inline-block; background: #378ADD; color: #fff;
                padding: 10px 20px; border-radius: 8px; text-decoration: none;
                font-size: 14px;">
        Abrir dashboard
      </a>
      <p style="color: #999; font-size: 12px; margin-top: 24px;">
        ML Market Research Automator
      </p>
    </div>
    """
