"""Easter egg endpoint -- x402-gated ($0.05 USDC on Base).

API key holders get free access. Public agents pay via x402.
Demonstrates the x402-gated access tier.
"""
import hashlib

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.shared.auth.middleware import has_valid_api_key
from src.shared.x402.config import (
    EASTER_EGG_PRICE, EASTER_EGG_DESCRIPTION,
    FACILITATOR_URL, NETWORK, PAY_TO, USDC_BASE,
)
from src.shared.x402.models import PaymentOption, PaymentRequirements
from src.services.easter_egg import get_easter_egg

router = APIRouter()


class EasterEggResponse(BaseModel):
    """Easter egg message response."""
    message: str = Field(description="Thank-you message for supporters")
    timestamp: str = Field(description="Server timestamp (ISO 8601)")


def _build_requirements() -> PaymentRequirements:
    return PaymentRequirements(
        accepts=[
            PaymentOption(
                scheme="exact",
                network=NETWORK,
                asset=USDC_BASE,
                pay_to=PAY_TO,
                max_amount_required=EASTER_EGG_PRICE,
                description=EASTER_EGG_DESCRIPTION,
                facilitator_url=FACILITATOR_URL,
            ),
        ],
        tool_name="easter_egg",
        tool_args_hash=hashlib.sha256(b"easter_egg").hexdigest(),
    )


@router.get(
    "/easter-egg",
    response_model=EasterEggResponse,
    summary="Easter egg (x402-gated)",
    description="Returns a thank-you message. Costs $0.05 USDC on Base for public agents. "
    "API key holders get free access. Returns 402 with payment requirements if no "
    "credentials are provided.",
    responses={
        200: {"description": "Easter egg message (authenticated or paid)"},
        402: {"description": "Payment required -- includes x402 payment options"},
    },
)
async def easter_egg(
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_payment_signature: str = Header(None, alias="X-Payment-Signature"),
):
    # API key holders get free access
    if has_valid_api_key(x_api_key):
        return get_easter_egg()

    # No payment proof -- return 402 with requirements
    if not x_payment_signature:
        requirements = _build_requirements()
        return JSONResponse(
            status_code=402,
            content={
                "payment_required": True,
                **requirements.model_dump(by_alias=True),
            },
        )

    # Payment signature provided -- in production, verify via facilitator
    # For the template, we accept any signature to demonstrate the flow
    return get_easter_egg()
