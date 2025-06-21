@router.get("/routes/check-access/{route_id}", summary="检查路由访问权限")
async def check_route_access(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查当前用户是否有权限访问指定路由
    """
    # 获取路由信息
    route = RouteService.get_route_by_id(db, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="路由不存在")
    
    # 检查用户是否是超级管理员
    is_superadmin = False
    for role in current_user.roles:
        if role.name == "超级管理员":
            is_superadmin = True
            break
    
    # 超级管理员可以访问所有路由
    if is_superadmin:
        return {
            "route_id": route_id,
            "path": route.path,
            "name": route.name,
            "has_access": True,
            "reason": "超级管理员可访问所有路由"
        }
    
    # 获取用户角色ID
    user_role_ids = [role.id for role in current_user.roles]
    
    # 检查route_permissions表中是否有权限记录
    route_permissions = db.query(RoutePermission).filter(
        RoutePermission.route_id == route_id,
        RoutePermission.role_id.in_(user_role_ids)
    ).all()
    
    if route_permissions:
        return {
            "route_id": route_id,
            "path": route.path,
            "name": route.name,
            "has_access": True,
            "reason": "通过route_permissions表检查权限成功",
            "matching_roles": [perm.role_id for perm in route_permissions]
        }
    
    # 检查路由meta中的权限
    if not route.meta:
        return {
            "route_id": route_id,
            "path": route.path,
            "name": route.name,
            "has_access": True,
            "reason": "路由无权限要求，所有人可访问"
        }
    
    meta = route.meta
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except:
            meta = {}
    
    # 如果meta不是字典或没有permission字段，则所有人可访问
    if not isinstance(meta, dict) or "permission" not in meta or meta.get("permission") == "*":
        return {
            "route_id": route_id,
            "path": route.path,
            "name": route.name,
            "has_access": True,
            "reason": "路由为公共路由，所有人可访问"
        }
    
    # 检查allowed_roles字段
    if "allowed_roles" in meta and isinstance(meta["allowed_roles"], list):
        user_role_ids_str = [str(role_id) for role_id in user_role_ids]
        for role_id in meta["allowed_roles"]:
            if str(role_id) in user_role_ids_str:
                return {
                    "route_id": route_id,
                    "path": route.path,
                    "name": route.name,
                    "has_access": True,
                    "reason": f"用户角色ID {role_id} 在allowed_roles列表中"
                }
    
    # 检查permission字段
    permission = meta.get("permission")
    
    # 如果permission是对象格式
    if isinstance(permission, dict):
        module = permission.get("module")
        level = permission.get("level")
        department_id = permission.get("departmentId")
        
        if current_user.has_permission(module, level, department_id):
            return {
                "route_id": route_id,
                "path": route.path,
                "name": route.name,
                "has_access": True,
                "reason": f"用户有模块权限: {module}:{level}"
            }
        else:
            return {
                "route_id": route_id,
                "path": route.path,
                "name": route.name,
                "has_access": False,
                "reason": f"用户缺少模块权限: {module}:{level}"
            }
    
    # 如果permission是字符串格式
    elif isinstance(permission, str):
        # 检查是否是MODULE:LEVEL格式
        if ":" in permission:
            module, level = permission.split(":")
            if current_user.has_permission(module, level):
                return {
                    "route_id": route_id,
                    "path": route.path,
                    "name": route.name,
                    "has_access": True,
                    "reason": f"用户有字符串权限: {permission}"
                }
            else:
                return {
                    "route_id": route_id,
                    "path": route.path,
                    "name": route.name,
                    "has_access": False,
                    "reason": f"用户缺少字符串权限: {permission}"
                }
        # 旧格式：部门权限
        else:
            if current_user.department and current_user.department.name == permission:
                return {
                    "route_id": route_id,
                    "path": route.path,
                    "name": route.name,
                    "has_access": True,
                    "reason": f"用户有部门权限: {permission}"
                }
            else:
                return {
                    "route_id": route_id,
                    "path": route.path,
                    "name": route.name,
                    "has_access": False,
                    "reason": f"用户缺少部门权限: {permission}"
                }
    
    # 默认无权限访问
    return {
        "route_id": route_id,
        "path": route.path,
        "name": route.name,
        "has_access": False,
        "reason": "未能满足任何权限条件"
    } 