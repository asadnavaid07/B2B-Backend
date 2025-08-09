# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from typing import List

# from app.core.database import get_db
# from app.models.categories import Category, ProductCategory
# from app.schema.category import ProductCategoryResponse
# from app.services.auth.jwt import role_required
# from app.schema.user import UserResponse

# category_router = APIRouter(tags=["categories"])


# @category_router.get("/user/categories", response_model=List[ProductCategoryResponse])
# async def get_selected_categories(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(ProductCategory).filter(ProductCategory.user_id == current_user.id).join(ProductCategory.category)
#     )
#     return result.scalars().all()


# @category_router.put("/user/categories", response_model=List[ProductCategoryResponse])
# async def update_selected_categories(
#     category_ids: List[int],
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     # Check all categories exist
#     result = await db.execute(select(Category).where(Category.id.in_(category_ids)))
#     valid_categories = result.scalars().all()
#     if len(valid_categories) != len(category_ids):
#         raise HTTPException(status_code=400, detail="One or more category IDs are invalid.")

#     # Delete old categories
#     await db.execute(
#         ProductCategory.__table__.delete().where(ProductCategory.user_id == current_user.id)
#     )

#     # Insert new categories
#     new_links = [
#         ProductCategory(user_id=current_user.id, category_id=cid)
#         for cid in category_ids
#     ]
#     db.add_all(new_links)
#     await db.commit()

#     # Fetch and return updated categories
#     result = await db.execute(
#         select(ProductCategory).filter(ProductCategory.user_id == current_user.id).join(ProductCategory.category)
#     )
#     return result.scalars().all()
