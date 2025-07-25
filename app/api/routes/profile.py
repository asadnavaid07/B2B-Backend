
# # Profile & Registration Routes
# @user_router.get("/profile", response_model=UserProfileResponse)
# async def get_profile(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer", "super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(UserProfile).filter(UserProfile.user_id == current_user.id))
#     profile = result.scalar_one_or_none()
#     if not profile:
#         raise HTTPException(status_code=404, detail="Profile not found")
#     return profile

# @user_router.put("/profile", response_model=UserProfileResponse)
# async def update_profile(
#     profile_data: UserProfileCreate,
#     current_user: UserResponse = Depends(role_required("vendor", "buyer", "super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(UserProfile).filter(UserProfile.user_id == current_user.id))
#     profile = result.scalar_one_or_none()
#     if not profile:
#         profile = UserProfile(user_id=current_user.id, **profile_data.dict())
#     else:
#         for key, value in profile_data.dict(exclude_unset=True).items():
#             setattr(profile, key, value)
#     db.add(profile)
#     await db.commit()
#     await db.refresh(profile)
#     return profile

# @user_router.post("/documents", response_model=DocumentResponse)
# async def upload_document(
#     document_type: str,
#     file: UploadFile = File(...),
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     file_path = f"uploads/{current_user.id}/{file.filename}"
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#     with open(file_path, "wb") as f:
#         f.write(file.file.read())
#     document = Document(
#         user_id=current_user.id,
#         document_type=document_type,
#         file_path=file_path,
#         verification_status=PlanStatus.PENDING_AI_VERIFICATION
#     )
#     db.add(document)
#     await db.commit()
#     await db.refresh(document)
#     return document

# @user_router.get("/documents", response_model=List[DocumentResponse])
# async def list_documents(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer", "super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(Document).filter(Document.user_id == current_user.id))
#     documents = result.scalars().all()
#     return documents

# @user_router.put("/documents/{document_id}", response_model=DocumentResponse)
# async def update_document(
#     document_id: int,
#     file: UploadFile = File(...),
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(Document).filter(Document.id == document_id, Document.user_id == current_user.id))
#     document = result.scalar_one_or_none()
#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")
#     file_path = f"uploads/{current_user.id}/{file.filename}"
#     with open(file_path, "wb") as f:
#         f.write(file.file.read())
#     document.file_path = file_path
#     document.verification_status = PlanStatus.PENDING_AI_VERIFICATION
#     db.add(document)
#     await db.commit()
#     await db.refresh(document)
#     return document

# @user_router.delete("/documents/{document_id}")
# async def delete_document(
#     document_id: int,
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(Document).filter(Document.id == document_id, Document.user_id == current_user.id))
#     document = result.scalar_one_or_none()
#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")
#     await db.delete(document)
#     await db.commit()
#     return {"message": "Document deleted successfully"}

# @user_router.get("/categories", response_model=List[str])
# async def get_categories(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(UserProfile).filter(UserProfile.user_id == current_user.id))
#     profile = result.scalar_one_or_none()
#     if not profile or not profile.product_categories:
#         return []
#     return profile.product_categories

# @user_router.put("/categories")
# async def update_categories(
#     categories: List[str],
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(UserProfile).filter(UserProfile.user_id == current_user.id))
#     profile = result.scalar_one_or_none()
#     if not profile:
#         raise HTTPException(status_code=404, detail="Profile not found")
#     profile.product_categories = categories
#     db.add(profile)
#     await db.commit()
#     return {"message": "Categories updated successfully"}

# # Plan & Level Management Routes
# @plan_router.get("/", response_model=List[Dict[str, any]])
# async def list_plans():
#     return [
#         {"plan_id": 1, "name": "Free", "price": 0, "level": 1},
#         {"plan_id": 2, "name": "Basic", "price": 5, "level": 2},
#         {"plan_id": 3, "name": "Standard", "price": 10, "level": 3},
#         {"plan_id": 4, "name": "Premium", "price": 15, "level": 4},
#         # Levels 5-8 are retention-based, not selectable
#     ]

# @plan_router.post("/select", response_model=UserPlanResponse)
# async def select_plan(
#     plan: UserPlanCreate,
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     if plan.plan_id not in [2, 3, 4]:
#         raise HTTPException(status_code=400, detail="Invalid plan ID")
#     user_plan = UserPlan(
#         user_id=current_user.id,
#         plan_id=plan.plan_id,
#         status=PlanStatus.PENDING_PAYMENT
#     )
#     db.add(user_plan)
#     await db.commit()
#     await db.refresh(user_plan)
#     # TODO: Integrate payment gateway
#     return user_plan

# @plan_router.post("/payment/verify")
# async def verify_payment(
#     plan_id: int,
#     payment_id: str,  # From external payment gateway
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(UserPlan).filter(UserPlan.user_id == current_user.id, UserPlan.plan_id == plan_id))
#     user_plan = result.scalar_one_or_none()
#     if not user_plan:
#         raise HTTPException(status_code=404, detail="Plan not found")
#     # TODO: Call external payment verification API
#     user_plan.status = PlanStatus.PAYMENT_VERIFIED
#     result = await db.execute(select(User).filter(User.id == current_user.id))
#     user = result.scalar_one_or_none()
#     user.plan_status = PlanStatus.PENDING_AI_VERIFICATION
#     db.add_all([user_plan, user])
#     await db.commit()
#     return {"message": "Payment verified, pending AI verification"}

# @plan_router.get("/status", response_model=UserPlanResponse)
# async def get_plan_status(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(UserPlan).filter(UserPlan.user_id == current_user.id))
#     user_plan = result.scalar_one_or_none()
#     if not user_plan:
#         raise HTTPException(status_code=404, detail="Plan not found")
#     return user_plan

# # AI Verification & KPI Routes
# @verification_router.get("/status", response_model=PlanStatus)
# async def get_verification_status(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(User).filter(User.id == current_user.id))
#     user = result.scalar_one_or_none()
#     return user.plan_status

# @verification_router.get("/kpi", response_model=Dict[str, any])
# async def get_kpi(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(User).filter(User.id == current_user.id))
#     user = result.scalar_one_or_none()
#     return {"kpi_score": user.kpi_score, "kpi_remarks": user.kpi_remarks}

# @verification_router.post("/reupload", response_model=DocumentResponse)
# async def reupload_document(
#     document_type: str,
#     file: UploadFile = File(...),
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     file_path = f"uploads/{current_user.id}/{file.filename}"
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#     with open(file_path, "wb") as f:
#         f.write(file.file.read())
#     document = Document(
#         user_id=current_user.id,
#         document_type=document_type,
#         file_path=file_path,
#         verification_status=PlanStatus.PENDING_AI_VERIFICATION
#     )
#     db.add(document)
#     await db.commit()
#     await db.refresh(document)
#     result = await db.execute(select(User).filter(User.id == current_user.id))
#     user = result.scalar_one_or_none()
#     user.plan_status = PlanStatus.AWAITING_ADDITIONAL_DOCUMENTS
#     db.add(user)
#     await db.commit()
#     return document

# # Dashboard Routes
# @dashboard_router.get("/status", response_model=DashboardResponse)
# async def get_dashboard_status(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(User).filter(User.id == current_user.id))
#     user = result.scalar_one_or_none()
#     return DashboardResponse(
#         registration_status=user.plan_status,
#         plan_level=user.plan_level,
#         kpi_score=user.kpi_score,
#         kpi_remarks=user.kpi_remarks,
#         retention_progress=user.retention_progress
#     )

# @dashboard_router.get("/kpi", response_model=Dict[str, any])
# async def get_dashboard_kpi(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(User).filter(User.id == current_user.id))
#     user = result.scalar_one_or_none()
#     return {"kpi_score": user.kpi_score, "kpi_remarks": user.kpi_remarks}

# @dashboard_router.get("/retention", response_model=float)
# async def get_retention_progress(
#     current_user: UserResponse = Depends(role_required("vendor", "buyer")),
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(select(User).filter(User.id == current_user.id))
#     user = result.scalar_one_or_none()
#     return user.retention_progress

# # Admin Panel Routes
# @admin_router.get("/users", response_model=List[UserResponse])
# async def list_users(
#     status: Optional[PlanStatus] = None,
#     level: Optional[int] = None,
#     kpi_min: Optional[float] = None,
#     current_user: UserResponse = Depends(role_required("super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     query = select(User)
#     if status:
#         query = query.filter(User.plan_status == status)
#     if level:
#         query = query.filter(User.plan_level == level)
#     if kpi_min:
#         query = query.filter(User.kpi_score >= kpi_min)
#     if current_user.role == "sub_admin" and current_user.ownership:
#         if "users" not in current_user.ownership.get("modules", []):
#             raise HTTPException(status_code=403, detail="Insufficient permissions")
#     result = await db.execute(query)
#     return result.scalars().all()

# @admin_router.get("/users/{user_id}", response_model=UserResponse)
# async def get_user_details(
#     user_id: int,
#     current_user: UserResponse = Depends(role_required("super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     if current_user.role == "sub_admin" and current_user.ownership:
#         if "users" not in current_user.ownership.get("modules", []):
#             raise HTTPException(status_code=403, detail="Insufficient permissions")
#     result = await db.execute(select(User).filter(User.id == user_id))
#     user = result.scalar_one_or_none()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# @admin_router.get("/users/{user_id}/documents", response_model=List[DocumentResponse])
# async def get_user_documents(
#     user_id: int,
#     current_user: UserResponse = Depends(role_required("super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     if current_user.role == "sub_admin" and current_user.ownership:
#         if "documents" not in current_user.ownership.get("modules", []):
#             raise HTTPException(status_code=403, detail="Insufficient permissions")
#     result = await db.execute(select(Document).filter(Document.user_id == user_id))
#     return result.scalars().all()

# @admin_router.get("/jobs")
# async def list_jobs(
#     current_user: UserResponse = Depends(role_required("super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     if current_user.role == "sub_admin" and current_user.ownership:
#         if "jobs" not in current_user.ownership.get("modules", []):
#             raise HTTPException(status_code=403, detail="Insufficient permissions")
#     # TODO: Implement job model and logic
#     return {"message": "Job listings not implemented"}

# @admin_router.post("/jobs")
# async def create_job(
#     job_data: Dict,  # TODO: Define JobCreate schema
#     current_user: UserResponse = Depends(role_required("super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     if current_user.role == "sub_admin" and current_user.ownership:
#         if "jobs" not in current_user.ownership.get("modules", []):
#             raise HTTPException(status_code=403, detail="Insufficient permissions")
#     # TODO: Implement job creation logic
#     return {"message": "Job creation not implemented"}

# @admin_router.put("/jobs/{job_id}")
# async def update_job(
#     job_id: int,
#     job_data: Dict,  # TODO: Define JobUpdate schema
#     current_user: UserResponse = Depends(role_required("super_admin", "sub_admin")),
#     db: AsyncSession = Depends(get_db)
# ):
#     if current_user.role == "sub_admin" and current_user.ownership:
#         if "jobs" not in current_user.ownership.get("modules", []):
#             raise HTTPException(status_code=403, detail="Insufficient permissions")
#     # TODO: Implement job update logic
#     return {"message": "Job update not implemented"}