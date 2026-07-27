from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Transaction, AccessLink
from config import settings


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    invited_by: Optional[int] = None
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        is_admin = telegram_id in settings.admin_id_list
        is_allowed = settings.FREE_ACCESS_MODE or is_admin or bool(invited_by)
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            is_allowed=is_allowed,
            invited_by=invited_by
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        # Update username/first_name if changed
        if user.username != username or user.first_name != first_name:
            user.username = username
            user.first_name = first_name
            await session.commit()
    return user


async def is_user_allowed(session: AsyncSession, telegram_id: int) -> bool:
    if telegram_id in settings.admin_id_list or settings.FREE_ACCESS_MODE:
        return True
    stmt = select(User.is_allowed).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    is_allowed = result.scalar_one_or_none()
    return bool(is_allowed)


async def set_user_allowed(session: AsyncSession, telegram_id: int, allowed: bool):
    stmt = update(User).where(User.telegram_id == telegram_id).values(is_allowed=allowed)
    await session.execute(stmt)
    await session.commit()


async def add_transaction(
    session: AsyncSession,
    user_id: int,
    tx_type: str,
    amount: float,
    category: str,
    description: Optional[str] = None,
    raw_text: Optional[str] = None,
    receipt_path: Optional[str] = None,
    date: Optional[datetime] = None
) -> Transaction:
    if date is None:
        date = datetime.utcnow()
    tx = Transaction(
        user_id=user_id,
        type=tx_type,
        amount=amount,
        category=category,
        description=description,
        raw_text=raw_text,
        receipt_path=receipt_path,
        date=date
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


async def get_transaction(session: AsyncSession, tx_id: int) -> Optional[Transaction]:
    stmt = select(Transaction).where(Transaction.id == tx_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def update_transaction(session: AsyncSession, tx_id: int, **kwargs) -> Optional[Transaction]:
    stmt = update(Transaction).where(Transaction.id == tx_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()
    return await get_transaction(session, tx_id)


async def delete_transaction(session: AsyncSession, tx_id: int) -> bool:
    stmt = delete(Transaction).where(Transaction.id == tx_id)
    res = await session.execute(stmt)
    await session.commit()
    return res.rowcount > 0


async def get_user_transactions(
    session: AsyncSession,
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tx_type: Optional[str] = None,
    limit: int = 50
) -> List[Transaction]:
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    if start_date:
        stmt = stmt.where(Transaction.date >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.date <= end_date)
    if tx_type:
        stmt = stmt.where(Transaction.type == tx_type)
    stmt = stmt.order_by(Transaction.date.desc()).limit(limit)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_period_summary(
    session: AsyncSession,
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    # Aggregated expense categories
    exp_stmt = (
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    exp_res = await session.execute(exp_stmt)
    expense_categories = {cat: float(total) for cat, total in exp_res.all()}

    # Aggregated income categories
    inc_stmt = (
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    inc_res = await session.execute(inc_stmt)
    income_categories = {cat: float(total) for cat, total in inc_res.all()}

    # Daily breakdown for charts
    daily_stmt = (
        select(
            func.strftime("%Y-%m-%d", Transaction.date).label("day"),
            Transaction.type,
            func.sum(Transaction.amount).label("total")
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        .group_by("day", Transaction.type)
        .order_by("day")
    )
    daily_res = await session.execute(daily_stmt)
    daily_data: Dict[str, Dict[str, float]] = {}
    for day, tx_type, total in daily_res.all():
        if day not in daily_data:
            daily_data[day] = {"expense": 0.0, "income": 0.0}
        daily_data[day][tx_type] = float(total)

    total_expense = sum(expense_categories.values())
    total_income = sum(income_categories.values())
    net_balance = total_income - total_expense

    return {
        "total_expense": total_expense,
        "total_income": total_income,
        "net_balance": net_balance,
        "expense_categories": expense_categories,
        "income_categories": income_categories,
        "daily_data": daily_data
    }


async def create_access_link(
    session: AsyncSession,
    created_by: int,
    code: str,
    max_uses: int = -1
) -> AccessLink:
    link = AccessLink(created_by=created_by, code=code, max_uses=max_uses)
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def validate_and_use_access_link(session: AsyncSession, code: str) -> bool:
    stmt = select(AccessLink).where(AccessLink.code == code, AccessLink.is_active == True)
    res = await session.execute(stmt)
    link = res.scalar_one_or_none()
    if not link:
        return False
    if link.max_uses != -1 and link.uses_count >= link.max_uses:
        link.is_active = False
        await session.commit()
        return False

    link.uses_count += 1
    if link.max_uses != -1 and link.uses_count >= link.max_uses:
        link.is_active = False
    await session.commit()
    return True
