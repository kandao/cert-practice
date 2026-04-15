"""
Exercise 4 — @field_validator (Pydantic v2)
============================================
Pattern  : pydantic.field_validator
Target   : ai-project/backend/routers/chat.py  →  ChatRequest
Time     : 20 min
Depends  : pydantic  (pip install pydantic)

PROBLEM
-------
The current ChatRequest in chat.py accepts any string for 'message' —
including empty strings and very long inputs. Validation belongs in the
model, not scattered across the handler as if-checks.

YOUR TASK
---------
1. Run this script — understand what each validator does.
2. Open ai-project/backend/routers/chat.py.
3. Add the two validators shown in APPLY_DIFF below.
4. Start the backend and verify via:
   curl -X POST http://localhost:8000/api/chat \\
        -H "Content-Type: application/json" \\
        -H "Authorization: Bearer <token>" \\
        -d '{"message": "   "}'
   Expected: HTTP 422 with clear error message.

JAVA ANALOGY
------------
Jakarta Bean Validation (@NotBlank, @Size) on a request DTO:

    public class ChatRequest {
        @NotBlank
        @Size(max = 8000)
        private String message;

        @Pattern(regexp = UUID_REGEX)
        private String sessionId;
    }

Pydantic defines constraints inline in the class, validated on instantiation.
"""

from pydantic import BaseModel, field_validator, ValidationError

MAX_MESSAGE_LENGTH = 8000


# ── The model ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

    @field_validator("message")
    @classmethod                    # REQUIRED in Pydantic v2.
    def message_not_blank(cls, v: str) -> str:
        """
        Why @classmethod?
        Pydantic calls validators before the model instance exists.
        There is no 'self' yet — only the class. @classmethod receives 'cls'.

        'v' = the raw field value before assignment.
        Return value REPLACES the original — returning stripped gives
        automatic whitespace trimming to all callers for free.

        Raising ValueError → FastAPI automatically returns HTTP 422.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("message cannot be blank")
        if len(stripped) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"message too long: {len(stripped)} chars (max {MAX_MESSAGE_LENGTH})"
            )
        return stripped

    @field_validator("session_id")
    @classmethod
    def session_id_valid_uuid(cls, v: str | None) -> str | None:
        """
        Pydantic skips this validator entirely when session_id is None.
        Only runs when a non-None value is provided.
        """
        if v is None:
            return v
        import uuid
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError(f"session_id must be a valid UUID, got: {v!r}")
        return v


# ── Demos ─────────────────────────────────────────────────────────────────────

def demo_valid():
    print("\n--- Valid inputs ---")

    r1 = ChatRequest(message="  hello world  ")
    print(f"  input:  '  hello world  '")
    print(f"  stored: '{r1.message}'")
    print(f"  ↑ whitespace stripped automatically by the validator's return value")

    r2 = ChatRequest(message="any message", session_id=None)
    print(f"\n  session_id=None  → passes (validator skipped)")

    r3 = ChatRequest(
        message="any message",
        session_id="550e8400-e29b-41d4-a716-446655440000"
    )
    print(f"  valid UUID       → passes: {r3.session_id}")


def demo_blank_message():
    print("\n--- Blank message → ValidationError ---")
    cases = ["", "   ", "\t\n"]
    for case in cases:
        try:
            ChatRequest(message=case)
        except ValidationError as e:
            errors = e.errors()
            print(f"  input={case!r:10}  → {errors[0]['msg']}")


def demo_long_message():
    print("\n--- Message too long → ValidationError ---")
    long_msg = "x" * (MAX_MESSAGE_LENGTH + 1)
    try:
        ChatRequest(message=long_msg)
    except ValidationError as e:
        print(f"  {len(long_msg)}-char message → {e.errors()[0]['msg']}")


def demo_invalid_uuid():
    print("\n--- Invalid session_id → ValidationError ---")
    cases = ["not-a-uuid", "123", "abc-def"]
    for case in cases:
        try:
            ChatRequest(message="hello", session_id=case)
        except ValidationError as e:
            print(f"  session_id={case!r:15} → {e.errors()[0]['msg']}")


def demo_v1_vs_v2():
    print("\n--- Pydantic v1 vs v2 — the @classmethod difference ---")
    print("""
  Pydantic v1 (old — still works but deprecated):
      @validator("message")
      def message_not_blank(cls, v):   # NO @classmethod needed
          ...

  Pydantic v2 (current):
      @field_validator("message")
      @classmethod                     # REQUIRED — omitting this raises a TypeError
      def message_not_blank(cls, v):
          ...

  This is the #1 mistake when migrating v1 validators to v2.
  """)


# ── Apply to ai-project ───────────────────────────────────────────────────────

APPLY_DIFF = """
CHANGES TO MAKE in ai-project/backend/routers/chat.py
=====================================================

CHANGE the import line:
    from pydantic import BaseModel
    →
    from pydantic import BaseModel, field_validator

REPLACE the ChatRequest class:
    class ChatRequest(BaseModel):
        message: str
        session_id: str | None = None

        @field_validator("message")
        @classmethod
        def message_not_blank(cls, v: str) -> str:
            stripped = v.strip()
            if not stripped:
                raise ValueError("message cannot be blank")
            if len(stripped) > 8000:
                raise ValueError(f"message too long: {len(stripped)} chars (max 8000)")
            return stripped

        @field_validator("session_id")
        @classmethod
        def session_id_valid_uuid(cls, v: str | None) -> str | None:
            if v is None:
                return v
            import uuid
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError(f"session_id must be a valid UUID, got: {v!r}")
            return v

VERIFY:
    curl -X POST http://localhost:8000/api/chat \\
         -H "Content-Type: application/json" \\
         -H "Authorization: Bearer <token>" \\
         -d '{"message": "   "}'
    # Expected: HTTP 422 with {"detail": [{"msg": "message cannot be blank", ...}]}
"""


if __name__ == "__main__":
    print(__doc__)
    demo_valid()
    demo_blank_message()
    demo_long_message()
    demo_invalid_uuid()
    demo_v1_vs_v2()
    print(APPLY_DIFF)
