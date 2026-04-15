"""
Exercise 8 — @model_validator (Pydantic v2)
============================================
Pattern  : pydantic.model_validator
Target   : ai-project/backend/routers/documents.py  →  list_documents()
Time     : 20 min
Depends  : pydantic  (pip install pydantic)

PROBLEM
-------
list_documents() validates 'page' and 'per_page' with inline if-statements:
    if page < 1:               page = 1
    if per_page < 1 ...: per_page = 20

This silently corrects bad input instead of rejecting it. The logic is buried
in the handler and cannot be reused or tested in isolation.

YOUR TASK
---------
1. Run this script — understand mode="after" vs mode="before".
2. Open ai-project/backend/routers/documents.py.
3. Add ListDocumentsQuery and refactor list_documents() as shown in APPLY_DIFF.

WHEN TO USE model_validator vs field_validator
----------------------------------------------
@field_validator:   your rule involves exactly ONE field.
@model_validator:   your rule involves TWO OR MORE fields, or the
                    relationship between them (e.g. end_date > start_date).

JAVA ANALOGY
------------
Class-level Bean Validation constraint:

    @ValidDateRange   // custom class-level constraint
    public class SearchRequest {
        private LocalDate from;
        private LocalDate to;
    }

    @Target(ElementType.TYPE)
    @Constraint(validatedBy = DateRangeValidator.class)
    public @interface ValidDateRange { ... }

Python's @model_validator is the same pattern with far less boilerplate.
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError


# ── The model ─────────────────────────────────────────────────────────────────

class ListDocumentsQuery(BaseModel):
    """
    Query parameters for GET /api/documents.
    FastAPI injects these from query string automatically via Depends().
    """
    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    status: str | None = Field(
        default=None,
        description="Filter by document status: processing | ready | failed",
    )

    @model_validator(mode="after")
    def validate_status_value(self) -> "ListDocumentsQuery":
        """
        mode="after":
          - Runs AFTER all individual fields are validated and coerced.
          - 'self' is the model instance — access fields as self.page, self.status.
          - Return self to pass, raise ValueError to reject.

        mode="before":
          - Receives the raw input dict BEFORE field coercion.
          - Use only when you need to rename keys or reshape the input.
          - Example: accept both 'page_num' and 'page' as the same field.
        """
        allowed = {"processing", "ready", "failed", None}
        if self.status not in allowed:
            raise ValueError(
                f"status must be one of {allowed - {None}}, got: {self.status!r}"
            )
        return self


# ── Demos ─────────────────────────────────────────────────────────────────────

def demo_valid():
    print("\n--- Valid inputs ---")

    cases = [
        {"page": 1, "per_page": 20},
        {"page": 3, "per_page": 50, "status": "ready"},
        {"page": 1, "per_page": 100, "status": "processing"},
        {},                                             # all defaults
    ]
    for kwargs in cases:
        q = ListDocumentsQuery(**kwargs)
        print(f"  {str(kwargs):<50} → page={q.page} per_page={q.per_page} status={q.status!r}")


def demo_field_constraints():
    print("\n--- Field-level constraints (ge=, le=) reject bad values ---")
    print("  These come from Field(ge=1, le=100) — no validator code needed.")

    cases = [
        {"page": 0},            # ge=1 fails
        {"per_page": 0},        # ge=1 fails
        {"per_page": 101},      # le=100 fails
        {"page": -5},           # ge=1 fails
    ]
    for kwargs in cases:
        try:
            ListDocumentsQuery(**kwargs)
        except ValidationError as e:
            print(f"  {str(kwargs):<25} → {e.errors()[0]['msg']}")


def demo_model_validator():
    print("\n--- @model_validator catches cross-field rule ---")

    try:
        ListDocumentsQuery(status="unknown_status")
    except ValidationError as e:
        print(f"  status='unknown_status' → {e.errors()[0]['msg']}")

    q = ListDocumentsQuery(status="ready")
    print(f"  status='ready' → OK: {q.status}")


def demo_mode_before():
    print("\n--- mode='before' vs mode='after' ---")

    class FlexibleQuery(BaseModel):
        page: int = 1

        @model_validator(mode="before")
        @classmethod
        def accept_page_num_alias(cls, data: dict) -> dict:
            """
            mode='before': receives raw dict, can rename keys before field validation.
            Use when the incoming data doesn't match your field names.
            """
            if "page_num" in data and "page" not in data:
                data["page"] = data.pop("page_num")
            return data

    q1 = FlexibleQuery(**{"page": 3})
    q2 = FlexibleQuery(**{"page_num": 5})     # alias accepted
    print(f"  page=3      → {q1.page}")
    print(f"  page_num=5  → {q2.page}   (mode='before' renamed the key)")

    print("""
  Summary:
    mode="after"  → self.field_name   (use for rules on coerced values)
    mode="before" → cls, data: dict   (use to reshape raw input)
  """)


def demo_refactored_handler():
    print("\n--- How the refactored list_documents handler looks ---")
    print("""
  # BEFORE (in documents.py):
  async def list_documents(page: int = 1, per_page: int = 20, ...):
      if page < 1:
          page = 1
      if per_page < 1 or per_page > 100:
          per_page = 20
      offset = (page - 1) * per_page
      ...

  # AFTER:
  async def list_documents(
      query: ListDocumentsQuery = Depends(),   # FastAPI injects query params
      ...
  ):
      offset = (query.page - 1) * query.per_page
      stmt = select(Document).where(Document.user_id == user.id)
      if query.status:
          stmt = stmt.where(Document.status == query.status)
      ...

  Benefits:
    - Validation is testable in isolation (just instantiate the model)
    - Invalid input is REJECTED (422) not silently corrected
    - Handler code is shorter and reads as business logic only
  """)


# ── Apply to ai-project ───────────────────────────────────────────────────────

APPLY_DIFF = """
CHANGES TO MAKE in ai-project/backend/routers/documents.py
===========================================================

ADD to imports:
    from pydantic import BaseModel, Field, model_validator

ADD this model before the router definition:
    class ListDocumentsQuery(BaseModel):
        page: int = Field(default=1, ge=1)
        per_page: int = Field(default=20, ge=1, le=100)
        status: str | None = Field(default=None)

        @model_validator(mode="after")
        def validate_status_value(self) -> "ListDocumentsQuery":
            allowed = {"processing", "ready", "failed", None}
            if self.status not in allowed:
                raise ValueError(f"status must be one of {allowed - {None}}, got: {self.status!r}")
            return self

CHANGE list_documents signature and body:
    @router.get("/")
    async def list_documents(
        query: ListDocumentsQuery = Depends(),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        rate_limiter: RateLimiter = Depends(get_rate_limiter),
    ) -> dict[str, Any]:
        await rate_limiter.check(str(user.id))
        offset = (query.page - 1) * query.per_page
        stmt = (
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(query.per_page)
        )
        if query.status:
            stmt = stmt.where(Document.status == query.status)
        # ... rest unchanged
"""


if __name__ == "__main__":
    print(__doc__)
    demo_valid()
    demo_field_constraints()
    demo_model_validator()
    demo_mode_before()
    demo_refactored_handler()
    print(APPLY_DIFF)
