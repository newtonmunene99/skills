from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Account:
    id: str
    status: str = "pending"
    balance: int = 0
    plan: str = "free"
    note: str = ""

    def open(self) -> Account:
        return replace(self, status="open")

    def close(self) -> Account:
        return replace(self, status="closed")

    def charge(self, amount: int) -> Account:
        return replace(self, balance=self.balance - amount)

    def refund(self, amount: int) -> Account:
        return replace(self, balance=self.balance + amount)

    def credit(self, amount: int) -> Account:
        return replace(self, balance=self.balance + amount)

    def debit(self, amount: int) -> Account:
        return replace(self, balance=self.balance - amount)

    def suspend(self, reason: str) -> Account:
        return replace(self, status="suspended", note=reason)

    def reinstate(self) -> Account:
        return replace(self, status="open", note="")

    def dispute(self, amount: int, reason: str) -> Account:
        return replace(self, status="disputed", balance=self.balance + amount, note=reason)

    def resolve_dispute(self, *, won: bool) -> Account:
        return replace(self, status="open" if won else "closed")

    def write_off(self, reason: str) -> Account:
        return replace(self, status="written_off", balance=0, note=reason)

    def change_plan(self, plan: str) -> Account:
        return replace(self, plan=plan)
