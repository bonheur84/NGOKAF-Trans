"""Finance controller for handling financial operations."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from database.session import get_session
from models.expense import Expense
from services import finance_service


class FinanceController:
    """Controller for finance-related operations."""

    def add_expense(
        self,
        date_paiement: date,
        categorie: str,
        montant: Decimal,
        description: str | None = None,
        mode_paiement: str = "especes",
        fournisseur: str | None = None,
        piece_jointe: str | None = None,
        created_by: int | None = None,
    ) -> tuple[bool, str, Expense | None]:
        """Add a new expense with validation."""
        session = get_session()
        try:
            if montant <= 0:
                return False, "Le montant doit être supérieur à 0", None

            if categorie not in Expense.CATEGORIES:
                return False, "Catégorie invalide.", None

            if mode_paiement not in Expense.MODES_PAIEMENT:
                return False, "Mode de paiement invalide.", None

            expense = finance_service.add_expense(
                session,
                date_paiement,
                categorie,
                montant,
                description,
                mode_paiement,
                fournisseur,
                piece_jointe,
                created_by,
            )
            return True, "Dépense ajoutée avec succès", expense
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'ajout: {str(e)}", None
        finally:
            session.close()

    def get_expenses(
        self,
        period: str = "day",
        start_date: date | None = None,
        end_date: date | None = None,
        categorie: str | None = None,
    ) -> list[Expense]:
        """Get expenses with filters."""
        session = get_session()
        try:
            return finance_service.get_expenses_by_period(
                session, period, start_date, end_date, categorie
            )
        finally:
            session.close()

    def get_financial_summary(
        self,
        period: str = "day",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Get financial summary for a period."""
        session = get_session()
        try:
            revenue = finance_service.get_revenue_by_period(session, period, start_date, end_date)
            expenses = finance_service.get_expenses_total_by_period(session, period, start_date, end_date)
            profit = revenue["total"] - expenses

            return {
                "revenue": revenue,
                "expenses": expenses,
                "profit": profit,
            }
        finally:
            session.close()

    def get_expenses_by_category(
        self,
        period: str = "day",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Decimal]:
        """Get expenses grouped by category."""
        session = get_session()
        try:
            return finance_service.get_expenses_by_category(session, period, start_date, end_date)
        finally:
            session.close()

    def get_daily_data(self, days: int = 30, end_date: date | None = None) -> list[dict]:
        """Get daily financial data for charts."""
        session = get_session()
        try:
            return finance_service.get_daily_financial_data(session, days, end_date)
        finally:
            session.close()

    def get_monthly_data(self, months: int = 12, end_date: date | None = None) -> list[dict]:
        """Get monthly financial data for charts."""
        session = get_session()
        try:
            return finance_service.get_monthly_financial_data(session, months, end_date)
        finally:
            session.close()

    def delete_expense(self, expense_id: int) -> tuple[bool, str]:
        """Delete an expense."""
        session = get_session()
        try:
            success = finance_service.delete_expense(session, expense_id)
            if success:
                return True, "Dépense supprimée avec succès"
            return False, "Dépense non trouvée"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la suppression: {str(e)}"
        finally:
            session.close()

    def get_expense_by_id(self, expense_id: int) -> Expense | None:
        """Get an expense by ID."""
        session = get_session()
        try:
            return finance_service.get_expense_by_id(session, expense_id)
        finally:
            session.close()

    def get_categories(self) -> list[str]:
        """Get available expense categories."""
        return Expense.CATEGORIES

    def get_payment_modes(self) -> list[str]:
        """Get available payment modes."""
        return Expense.MODES_PAIEMENT
