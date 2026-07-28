"""Finance service for financial tracking and reporting."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.expense import Expense
from models.luggage import Luggage
from models.ticket import Ticket


def _money(v) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(v)


def add_expense(
    session: Session,
    date_paiement: date,
    categorie: str,
    montant: Decimal,
    description: str | None = None,
    mode_paiement: str = "especes",
    fournisseur: str | None = None,
    piece_jointe: str | None = None,
    created_by: int | None = None,
) -> Expense:
    """Add a new expense to the database."""
    from models.user import User
    valid_creator_id = None
    if created_by and session.query(User).filter(User.id == created_by).first():
        valid_creator_id = created_by
    else:
        first_user = session.query(User).first()
        if first_user:
            valid_creator_id = first_user.id

    expense = Expense(
        date_paiement=date_paiement,
        categorie=categorie,
        montant=montant,
        description=description,
        mode_paiement=mode_paiement,
        fournisseur=fournisseur,
        piece_jointe=piece_jointe,
        created_by=valid_creator_id,
    )
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


def get_expenses_by_period(
    session: Session,
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
    categorie: str | None = None,
) -> list[Expense]:
    """Get expenses filtered by period and optionally category."""
    query = session.query(Expense)
    
    if period == "day":
        target_date = start_date or date.today()
        query = query.filter(Expense.date_paiement == target_date)
    elif period == "week":
        if start_date is None:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        if end_date is None:
            end_date = start_date + timedelta(days=6)
        query = query.filter(Expense.date_paiement >= start_date, Expense.date_paiement <= end_date)
    elif period == "month":
        if start_date is None:
            today = date.today()
            start_date = date(today.year, today.month, 1)
        if end_date is None:
            end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
        query = query.filter(Expense.date_paiement >= start_date, Expense.date_paiement <= end_date)
    elif period == "year":
        if start_date is None:
            today = date.today()
            start_date = date(today.year, 1, 1)
        if end_date is None:
            end_date = date(start_date.year, 12, 31)
        query = query.filter(Expense.date_paiement >= start_date, Expense.date_paiement <= end_date)
    elif start_date and end_date:
        query = query.filter(Expense.date_paiement >= start_date, Expense.date_paiement <= end_date)
    
    if categorie:
        query = query.filter(Expense.categorie == categorie)
    
    return query.order_by(Expense.date_paiement.desc()).all()


def get_revenue_by_period(
    session: Session,
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Calculate detailed revenue (tickets + luggage) for a period."""
    if period == "day":
        target_date = start_date or date.today()
        ticket_rev = (
            session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id))
            .filter(Ticket.date_vente == target_date, Ticket.statut == "vendu")
            .one()
        )
        luggage_rev = (
            session.query(func.coalesce(func.sum(Luggage.total), 0), func.count(Luggage.id))
            .filter(func.date(Luggage.created_at) == target_date)
            .one()
        )
    elif period == "week":
        if start_date is None:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        if end_date is None:
            end_date = start_date + timedelta(days=6)
        ticket_rev = (
            session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id))
            .filter(
                Ticket.date_vente >= start_date,
                Ticket.date_vente <= end_date,
                Ticket.statut == "vendu",
            )
            .one()
        )
        luggage_rev = (
            session.query(func.coalesce(func.sum(Luggage.total), 0), func.count(Luggage.id))
            .filter(
                func.date(Luggage.created_at) >= start_date,
                func.date(Luggage.created_at) <= end_date,
            )
            .one()
        )
    elif period == "month":
        if start_date is None:
            today = date.today()
            start_date = date(today.year, today.month, 1)
        if end_date is None:
            end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
        ticket_rev = (
            session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id))
            .filter(
                Ticket.date_vente >= start_date,
                Ticket.date_vente <= end_date,
                Ticket.statut == "vendu",
            )
            .one()
        )
        luggage_rev = (
            session.query(func.coalesce(func.sum(Luggage.total), 0), func.count(Luggage.id))
            .filter(
                func.date(Luggage.created_at) >= start_date,
                func.date(Luggage.created_at) <= end_date,
            )
            .one()
        )
    elif period == "year":
        if start_date is None:
            today = date.today()
            start_date = date(today.year, 1, 1)
        if end_date is None:
            end_date = date(start_date.year, 12, 31)
        ticket_rev = (
            session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id))
            .filter(
                Ticket.date_vente >= start_date,
                Ticket.date_vente <= end_date,
                Ticket.statut == "vendu",
            )
            .one()
        )
        luggage_rev = (
            session.query(func.coalesce(func.sum(Luggage.total), 0), func.count(Luggage.id))
            .filter(
                func.date(Luggage.created_at) >= start_date,
                func.date(Luggage.created_at) <= end_date,
            )
            .one()
        )
    elif start_date and end_date:
        ticket_rev = (
            session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id))
            .filter(
                Ticket.date_vente >= start_date,
                Ticket.date_vente <= end_date,
                Ticket.statut == "vendu",
            )
            .one()
        )
        luggage_rev = (
            session.query(func.coalesce(func.sum(Luggage.total), 0), func.count(Luggage.id))
            .filter(
                func.date(Luggage.created_at) >= start_date,
                func.date(Luggage.created_at) <= end_date,
            )
            .one()
        )
    else:
        ticket_rev = (Decimal("0"), 0)
        luggage_rev = (Decimal("0"), 0)
    
    return {
        "total": _money(ticket_rev[0]) + _money(luggage_rev[0]),
        "tickets": {
            "amount": _money(ticket_rev[0]),
            "count": int(ticket_rev[1] or 0),
        },
        "luggage": {
            "amount": _money(luggage_rev[0]),
            "count": int(luggage_rev[1] or 0),
        },
    }


def get_expenses_total_by_period(
    session: Session,
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
    categorie: str | None = None,
) -> Decimal:
    """Calculate total expenses for a period."""
    expenses = get_expenses_by_period(session, period, start_date, end_date, categorie)
    return sum(exp.montant for exp in expenses)


def get_financial_summary(
    session: Session,
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Get financial summary including revenue, expenses, and profit."""
    revenue = get_revenue_by_period(session, period, start_date, end_date)
    expenses = get_expenses_total_by_period(session, period, start_date, end_date)
    profit = revenue - expenses
    
    return {
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
    }


def get_expenses_by_category(
    session: Session,
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Decimal]:
    """Get expenses grouped by category for a period."""
    expenses = get_expenses_by_period(session, period, start_date, end_date)
    category_totals: dict[str, Decimal] = {}
    
    for exp in expenses:
        category_totals[exp.categorie] = category_totals.get(exp.categorie, Decimal("0")) + exp.montant
    
    return category_totals


def get_daily_financial_data(
    session: Session,
    days: int = 30,
    end_date: date | None = None,
) -> list[dict]:
    """Get daily financial data for charts (revenue, expenses, profit)."""
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    data = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        revenue = get_revenue_by_period(session, "day", current_date, current_date)
        expenses = get_expenses_total_by_period(session, "day", current_date, current_date)
        profit = revenue - expenses
        
        data.append({
            "date": current_date,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
        })
    
    return data


def get_monthly_financial_data(
    session: Session,
    months: int = 12,
    end_date: date | None = None,
) -> list[dict]:
    """Get monthly financial data for charts."""
    end_date = end_date or date.today()
    
    data = []
    for i in range(months):
        # Calculate month start and end
        year = end_date.year
        month = end_date.month - i
        if month <= 0:
            month += 12
            year -= 1
        
        start_date = date(year, month, 1)
        if month == 12:
            end_month = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_month = date(year, month + 1, 1) - timedelta(days=1)
        
        revenue = get_revenue_by_period(session, "month", start_date, end_month)
        expenses = get_expenses_total_by_period(session, "month", start_date, end_month)
        profit = revenue - expenses
        
        data.append({
            "date": start_date,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
        })
    
    return list(reversed(data))


def delete_expense(session: Session, expense_id: int) -> bool:
    """Delete an expense by ID."""
    expense = session.query(Expense).filter(Expense.id == expense_id).first()
    if expense:
        session.delete(expense)
        session.commit()
        return True
    return False


def get_expense_by_id(session: Session, expense_id: int) -> Expense | None:
    """Get an expense by ID."""
    return session.query(Expense).filter(Expense.id == expense_id).first()
