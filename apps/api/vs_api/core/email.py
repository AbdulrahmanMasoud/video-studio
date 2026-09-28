"""Transactional email: SMTP (Mailpit in dev) or Resend (prod). Plain text + minimal HTML, bilingual subject lines by locale."""
from __future__ import annotations

import json
import logging
import smtplib
import urllib.request
from email.message import EmailMessage

from ..config import get_settings

log = logging.getLogger("vs_api.email")

TEXTS = {
    "verify": {"en": ("Verify your {app} email", "Welcome to {app}! Confirm your email:\n\n{link}\n\nThe link is valid for 24 hours."),
               "ar": ("تأكيد بريدك في {app}", "أهلاً بك في {app}! أكّد بريدك الإلكتروني:\n\n{link}\n\nالرابط صالح لمدة 24 ساعة.")},
    "reset": {"en": ("Reset your {app} password", "Reset your password with this link:\n\n{link}\n\nIf you did not ask for this, ignore this email."),
              "ar": ("إعادة تعيين كلمة مرور {app}", "أعد تعيين كلمة المرور من هذا الرابط:\n\n{link}\n\nإذا لم تطلب ذلك، تجاهل هذه الرسالة.")},
    "render_done": {"en": ("Your video is ready: {title}", "Your video \"{title}\" is ready to download:\n\n{link}"),
                    "ar": ("فيديوك جاهز: {title}", "فيديو \"{title}\" جاهز للتحميل:\n\n{link}")},
    "render_failed": {"en": ("We could not finish: {title}", "Rendering \"{title}\" failed ({code}). Your credits were released.\n\n{link}"),
                      "ar": ("تعذّر إكمال: {title}", "فشل إنتاج \"{title}\" ({code}). تم إرجاع رصيدك.\n\n{link}")},
    "payment_failed": {"en": ("Payment failed for {app}", "Your last payment failed. Update your payment method:\n\n{link}"),
                       "ar": ("فشل الدفع في {app}", "فشلت آخر عملية دفع. حدّث وسيلة الدفع:\n\n{link}")},
}


def render(kind: str, locale: str, **kw) -> tuple[str, str]:
    subj, body = TEXTS[kind].get(locale.split("-")[0], TEXTS[kind]["en"])
    kw = {"app": get_settings().app_name, **kw}
    return subj.format(**kw), body.format(**kw)


def send(to: str, kind: str, locale: str = "en", **kw) -> bool:
    subject, body = render(kind, locale, **kw)
    s = get_settings()
    try:
        if s.email_provider == "resend" and s.resend_api_key:
            req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps({"from": s.email_from, "to": [to], "subject": subject, "text": body}).encode(),
                                         headers={"Authorization": f"Bearer {s.resend_api_key}", "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15):
                return True
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = s.email_from, to, subject
        msg.set_content(body)
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)
        return True
    except Exception as e:  # email must never break a request
        log.warning("email %s to %s failed: %s", kind, to, e)
        return False
