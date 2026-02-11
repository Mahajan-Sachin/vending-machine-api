from sqlalchemy.orm import Session

from app.config import settings
from sqlalchemy import and_
from app.models import Item, Slot

def purchase(db: Session, item_id: str, cash_inserted: int) -> dict:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise ValueError("item_not_found")

    if cash_inserted < item.price:
        raise ValueError("insufficient_cash", item.price, cash_inserted)

    slot_id = item.slot_id
    price = item.price

    # Atomic item update
    updated_rows = (
        db.query(Item)
        .filter(and_(Item.id == item_id, Item.quantity > 0))
        .update({Item.quantity: Item.quantity - 1}, synchronize_session=False)
    )

    if updated_rows == 0:
        raise ValueError("out_of_stock")

    # Atomic slot update
    db.query(Slot).filter(Slot.id == slot_id).update(
        {Slot.current_item_count: Slot.current_item_count - 1},
        synchronize_session=False
    )

    db.commit()

    updated_item = db.query(Item).filter(Item.id == item_id).first()

    change = cash_inserted - price

    return {
        "item": updated_item.name,
        "price": price,
        "cash_inserted": cash_inserted,
        "change_returned": change,
        "remaining_quantity": updated_item.quantity,
        "message": "Purchase successful",
    }


def change_breakdown(change: int) -> dict:
    denominations = sorted(settings.SUPPORTED_DENOMINATIONS, reverse=True)
    result: dict[str, int] = {}
    remaining = change
    for d in denominations:
        if remaining <= 0:
            break
        count = remaining // d
        if count > 0:
            result[str(d)] = count
            remaining -= count * d
    return {"change": change, "denominations": result}
