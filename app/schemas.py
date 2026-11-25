"""Request schemas for the prediction API.

Bounds are the observed limits of the processed training cohort, not clinical
reference intervals. See ``model/MODEL_CARD.md`` for their provenance.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionInput(BaseModel):
    """The six raw values supplied by a dashboard user."""

    model_config = ConfigDict(allow_inf_nan=False)

    pT217_F: float = Field(
        ge=0.030,
        le=1.938,
        description="pT217_F; unit not documented in the supplied data.",
    )
    AB42_AB40_F: float = Field(
        ge=0.0615,
        le=0.1323,
        description="Aβ42/Aβ40 ratio.",
    )
    GFAP_Q: float = Field(
        ge=33.1,
        le=430.7,
        description="GFAP_Q; unit not documented in the supplied data.",
    )
    AGE: float = Field(ge=51.014374, le=91.137577, description="Age in years.")
    APOE4: Literal[0, 1] = Field(
        description="APOE ε4 carrier status: 0 = non-carrier, 1 = carrier.",
    )
    SEX: Literal[0, 1] = Field(description="Sex code: 0 = female, 1 = male.")


class TopFactor(BaseModel):
    """One deterministic local sensitivity contribution."""

    feature: str
    contribution: float


class PredictionResponse(BaseModel):
    """The public response of the isolated prediction endpoint."""

    probability: float
    category: str
    top_factors: list[TopFactor]
    model_version: str


class ChatHistoryMessage(BaseModel):
    """A browser-only chat turn. It is never sent to the prediction path."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    """The deliberately small, prediction-free chatbot request body."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=20)


class ChatSource(BaseModel):
    """One PDF page used as chat context."""

    doc: str
    page: int


class ChatResponse(BaseModel):
    """An educational response and its retrievable local sources."""

    answer: str
    sources: list[ChatSource]
