"""Approval e-mailer for the registration workflow.

Sends an approval "ticket" to administrators when a new account registers.
Transport is SMTP configured through environment variables:

* ``SMTP_HOST`` / ``SMTP_PORT`` / ``SMTP_USER`` / ``SMTP_PASSWORD``
* ``MAIL_FROM`` - sender address
* ``MAIL_APPROVAL_RECIPIENTS`` - optional comma-separated recipients;
  when empty, every Admin/Administrator account is notified.

When SMTP is not configured the delivery attempt is skipped and reported as
``delivered=False`` so callers can log a warning and keep working (the pending
approval remains visible to admins under Settings > Users).
"""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText

from config import settings as platform_settings

log = logging.getLogger("mailer")

SELF_SIGNED_OK = ("STARTTLS", "TLS", "SSL", "tls", "ssl")


def smtp_configured():
    return bool((platform_settings.SMTP_HOST or "").strip())


def resolve_recipients():
    """Return the e-mail addresses to notify for approval requests."""
    configured = (platform_settings.MAIL_APPROVAL_RECIPIENTS or "").strip()
    if configured:
        return [
            address.strip()
            for address in configured.split(",")
            if address.strip()
        ]

    from services import users_service

    return [
        admin["email"]
        for admin in users_service.list_admins()
        if admin.get("email")
    ]


def _smtp_connect():
    host = (platform_settings.SMTP_HOST or "").strip()
    port = int(getattr(platform_settings, "SMTP_PORT", 587) or 587)
    user = (platform_settings.SMTP_USER or "").strip()
    password = platform_settings.SMTP_PASSWORD or ""
    use_tls = bool(getattr(platform_settings, "SMTP_USE_TLS", True))

    context = ssl.create_default_context()
    server = smtplib.SMTP(host, port, timeout=15)
    server.ehlo()
    if use_tls:
        try:
            server.starttls(context=context)
            server.ehlo()
        except ssl.SSLError:
            server = smtplib.SMTP(host, port, timeout=15)
            server.ehlo()
            server.starttls(context=ssl._create_unverified_context())
            server.ehlo()
    if user and password:
        server.login(user, password)
    return server


def send_approval_ticket(candidate, base_url=""):
    """Notify administrators of a new account waiting for approval.

    ``candidate`` is the public user dict created during registration.
    Returns a dict::

        {"delivered": bool, "to": [...], "reason": optional str}
    """
    recipient_emails = resolve_recipients()
    if not smtp_configured() or not recipient_emails:
        return {
            "delivered": False,
            "to": recipient_emails,
            "reason": (
                "SMTP is not configured; approval pending in Settings > Users."
                if not smtp_configured()
                else "No admin recipients configured."
            ),
        }

    subject = (
        "New account pending approval: {0} <{1}>".format(
            candidate.get("name") or "Unknown", candidate.get("email") or "?"
        )
    )

    body = (
        "A new account is waiting for approval.\n\n"
        "Name: {name}\n"
        "Email: {email}\n"
        "Requested role: {role}\n"
        "Requested at: {created}\n\n"
        "Open Settings > Users in the platform to approve or reject "
        "this account.\n"
        "Review link: {link}\n"
    ).format(
        name=candidate.get("name") or "",
        email=candidate.get("email") or "",
        role=candidate.get("role") or "",
        created=candidate.get("created") or "",
        link=((base_url or "").rstrip("/") + "/settings"),
    )

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = platform_settings.MAIL_FROM
    message["To"] = ", ".join(recipient_emails)

    try:
        server = _smtp_connect()
        try:
            server.sendmail(
                platform_settings.MAIL_FROM,
                recipient_emails,
                message.as_string(),
            )
        finally:
            try:
                server.quit()
            except Exception:
                pass
        return {"delivered": True, "to": recipient_emails, "reason": None}
    except Exception as exc:
        log.warning(
            "Approval e-mail to %s failed: %s",
            recipient_emails,
            exc,
        )
        return {
            "delivered": False,
            "to": recipient_emails,
            "reason": str(exc)[:200],
        }


def send_demo_notification(lead, base_url=""):
    """Notify administrators when a demo is requested from the landing page.

    ``lead`` is the public demo-request dict created by the signup flow.
    Returns a dict::

        {"delivered": bool, "to": [...], "reason": optional str}
    """
    recipient_emails = resolve_recipients()
    if not smtp_configured() or not recipient_emails:
        return {
            "delivered": False,
            "to": recipient_emails,
            "reason": (
                "SMTP is not configured; demo request logged."
                if not smtp_configured()
                else "No admin recipients configured."
            ),
        }

    subject = "Demo request: {0} <{1}>".format(
        lead.get("name") or "Unknown", lead.get("email") or "?"
    )

    body = (
        "A new demo was requested from the landing page.\n\n"
        "Name: {name}\n"
        "Email: {email}\n"
        "Company: {company}\n"
        "Role: {role}\n"
        "Message:\n{message}\n\n"
        "Review link: {link}\n"
    ).format(
        name=lead.get("name") or "",
        email=lead.get("email") or "",
        company=lead.get("company") or "",
        role=lead.get("role") or "",
        message=lead.get("message") or "",
        link=((base_url or "").rstrip("/") + "/settings"),
    )

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = platform_settings.MAIL_FROM
    message["To"] = ", ".join(recipient_emails)

    try:
        server = _smtp_connect()
        try:
            server.sendmail(
                platform_settings.MAIL_FROM,
                recipient_emails,
                message.as_string(),
            )
        finally:
            try:
                server.quit()
            except Exception:
                pass
        return {"delivered": True, "to": recipient_emails, "reason": None}
    except Exception as exc:
        log.warning(
            "Demo notification e-mail to %s failed: %s",
            recipient_emails,
            exc,
        )
        return {
            "delivered": False,
            "to": recipient_emails,
            "reason": str(exc)[:200],
        }
