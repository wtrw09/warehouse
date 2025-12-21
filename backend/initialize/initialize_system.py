"""
系统初始化配置服务
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, text
from models.system.system_init import SystemInit, SystemConfig
from models.account.permission import Permission as PermissionModel
from models.account.role import Role
from models.base.major import Major
from models.base.sub_major import SubMajor
from models.base.equipment import Equipment
from models.system.material_code_level import MaterialCodeLevel
from core.security import Permission, PERMISSION_DESCRIPTIONS
from datetime import datetime
# 统一使用database.py的引擎和初始化函数
from database import init_db, get_engine, check_database_exists, get_session
from database import get_system_config_engine, init_system_config_db, check_system_config_db_exists

# 使用database.py的引擎
# 主数据库引擎缓存
main_db_engine = None

# 系统配置数据库引擎缓存
system_config_db_engine = None

def get_main_db_engine():
    """
    获取主数据库引擎实例（带缓存）
    统一使用database.py的引擎，避免重复创建
    """
    global main_db_engine
    if main_db_engine is None:
        main_db_engine = get_engine()
    return main_db_engine

def get_system_config_db_engine():
    """
    获取系统配置数据库引擎实例（带缓存）
    统一使用database_system_config.py的引擎，避免重复创建
    """
    global system_config_db_engine
    if system_config_db_engine is None:
        system_config_db_engine = get_system_config_engine()
    return system_config_db_engine

# 检查数据库文件是否存在（现在使用database.py的函数）
# check_database_exists 已移到 database.py

def is_main_db_initialized():
    """检查主数据库是否已初始化"""
    try:
        # 检查主数据库是否存在
        if not check_database_exists():
            return False
            
        engine = get_main_db_engine()
        with Session(engine) as db:
            # 检查主数据库的系统初始化表是否存在记录
            init_record = db.exec(select(SystemInit)).first()
            # 检查initialized字段是否为True
            return init_record is not None and init_record.initialized
    except Exception as e:
        print(f"❌ 检查主数据库初始化状态失败: {e}")
        return False

def is_system_config_db_initialized():
    """检查系统配置数据库是否已初始化"""
    try:
        # 检查系统配置数据库是否存在
        if not check_system_config_db_exists():
            return False
            
        engine = get_system_config_db_engine()
        with Session(engine) as db:
            # 检查系统配置数据库的系统初始化表是否存在记录
            init_record = db.exec(select(SystemInit)).first()
            # 不仅要检查记录是否存在，还要检查initialized字段是否为True
            return init_record is not None and init_record.initialized
    except Exception as e:
        print(f"❌ 检查系统配置数据库初始化状态失败: {e}")
        return False

def is_system_initialized():
    """检查系统是否已初始化（两个数据库都必须初始化）"""
    main_db_initialized = is_main_db_initialized()
    system_config_db_initialized = is_system_config_db_initialized()
    
    print(f"📊 主数据库初始化状态: {'已初始化' if main_db_initialized else '未初始化'}")
    print(f"📊 系统配置数据库初始化状态: {'已初始化' if system_config_db_initialized else '未初始化'}")
    
    return main_db_initialized and system_config_db_initialized

def initialize_system_config():
    """初始化系统配置"""
    
    print("🔍 检查系统配置数据库初始化状态...")
    
    # 检查系统配置数据库的初始化状态
    system_config_db_initialized = is_system_config_db_initialized()
    
    print(f"📊 系统配置数据库初始化状态: {'已初始化' if system_config_db_initialized else '未初始化'}")
    
    # 如果系统配置数据库已初始化，则跳过
    if system_config_db_initialized:
        print("⚠ 系统配置数据库已初始化，跳过配置初始化")
        return
    
    # 初始化系统配置数据库（如果未初始化）
    if not system_config_db_initialized:
        print("\n⚙️ 开始初始化系统配置数据库...")
        
        # 连接系统配置数据库
        engine = get_system_config_engine()
        # 清空系统配置数据库中的所有表
        init_system_config_db()
        
        with Session(engine) as db:
            try:
              
                # 先检查是否已有记录，如果有则更新，否则创建新记录
                existing_record = db.exec(select(SystemInit)).first()
                
                if existing_record:
                    # 更新现有记录
                    existing_record.initialized = True
                    existing_record.init_time = datetime.now()
                    existing_record.init_version = "1.0.0"
                    db.add(existing_record)
                    print("✓ 更新系统初始化记录")
                else:
                    # 创建新的系统初始化记录
                    init_record = SystemInit(
                        initialized=True,
                        init_time=datetime.now(),
                        init_version="1.0.0"
                    )
                    db.add(init_record)
                    print("✓ 创建系统初始化记录")
                
                # 从config.py读取默认配置
                from core.config import DynamicSettings
                
                # 创建DynamicSettings实例获取默认配置
                dynamic_settings = DynamicSettings()
                default_configs = dynamic_settings._defaults
                
                # 构建配置项
                config_items = []
                for key, value in default_configs.items():
                    # 确定配置类型
                    if isinstance(value, bool):
                        config_type = 'bool'
                        value_str = str(value).lower()
                    elif isinstance(value, int):
                        config_type = 'int'
                        value_str = str(value)
                    else:
                        config_type = 'string'
                        value_str = str(value)
                    
                    # 添加描述
                    description = None
                    if key == "SECRET_KEY":
                        description = "JWT密钥"
                    elif key == "ALGORITHM":
                        description = "JWT算法"
                    elif key == "AUTH_STRATEGY":
                        description = "认证策略 (jwt_fixed/sliding_session)"
                    elif key == "ACCESS_TOKEN_EXPIRE_MINUTES":
                        description = "JWT访问令牌过期时间(分钟)"
                    elif key == "SLIDING_SESSION_TIMEOUT_MINUTES":
                        description = "滑动会话超时时间(分钟)"
                    elif key == "ACCESS_TOKEN_SHORT_EXPIRE_MINUTES":
                        description = "短期访问令牌过期时间(分钟)"
                    elif key == "REDIS_URL":
                        description = "Redis连接URL"
                    elif key == "ADMIN_INVITATION_CODE":
                        description = "管理员邀请码"
                    
                    config_items.append({
                        'key': key,
                        'value': value_str,
                        'type': config_type,
                        'description': description
                    })
                
                # 创建系统配置记录
                current_time = datetime.now()
                for item in config_items:
                    # 检查配置项是否已存在
                    existing_config = db.exec(select(SystemConfig).where(SystemConfig.config_key == item['key'])).first()
                    if existing_config:
                        # 更新现有配置
                        existing_config.config_value = item['value']
                        existing_config.config_type = item['type']
                        existing_config.description = item['description']
                        existing_config.updated_time = current_time
                        existing_config.is_active = True
                        db.add(existing_config)
                        print(f"✓ 更新配置: {item['key']} = {item['value']}")
                    else:
                        # 创建新配置
                        config = SystemConfig(
                            config_key=item['key'],
                            config_value=item['value'],
                            config_type=item['type'],
                            description=item['description'],
                            created_time=current_time,
                            updated_time=current_time,
                            is_active=True
                        )
                        db.add(config)
                        print(f"✓ 创建配置: {item['key']} = {item['value']}")
                
                # 提交事务
                db.commit()
                
                print(f"✅ 系统配置数据库初始化完成！")
                print(f"📊 初始化时间: {datetime.now()}")
                
            except Exception as e:
                db.rollback()
                print(f"❌ 系统配置数据库初始化失败: {e}")
                raise
    else:
        print("✅ 系统配置数据库已初始化，跳过")
    
    print(f"\n🎉 系统配置初始化完成！")
    print(f"📊 完成时间: {datetime.now()}")

def get_system_config():
    """获取系统配置"""
    try:
        engine = get_system_config_engine()
        with Session(engine) as db:
            # 使用原生SQL查询获取系统配置
            query = text("SELECT config_key, config_value, config_type FROM _system_config WHERE is_active = 1")
            result = db.exec(query)
            configs = result.fetchall()
            
            config_dict = {}
            for config in configs:
                # 根据类型转换值
                if config.config_type == 'int':
                    config_dict[config.config_key] = int(config.config_value)
                elif config.config_type == 'bool':
                    config_dict[config.config_key] = config.config_value.lower() == 'true'
                else:
                    config_dict[config.config_key] = config.config_value
            
            return config_dict
    except Exception as e:
        print(f"获取系统配置时出错: {e}")
        return {}

def update_system_config(config_key: str, config_value: str):
    """更新系统配置"""
    try:
        engine = get_system_config_engine()
        with Session(engine) as db:
            # 使用原生SQL更新配置
            update_query = text("""
                UPDATE _system_config 
                SET config_value = :config_value, updated_time = :updated_time 
                WHERE config_key = :config_key
            """)
            
            db.exec(update_query, {
                "config_value": config_value,
                "updated_time": datetime.now(),
                "config_key": config_key
            })
            db.commit()
            print(f"✓ 更新配置: {config_key} = {config_value}")
            return True
    except Exception as e:
        print(f"更新系统配置时出错: {e}")
        return False

def initialize_permissions_and_roles(db: Session):
    """初始化权限和角色"""
    print("\n🔐 开始初始化权限和角色...")
    
    # 从security.py导入的权限定义生成权限列表
    permissions = [
        PermissionModel(id=Permission.AUTH_EDIT.value, name="用户和权限编辑", description="可以修改系统中任意用户的信息和权限"),
        PermissionModel(id=Permission.AUTH_READ.value, name="查看用户信息", description="可以查看系统中任意用户的信息"),
        PermissionModel(id=Permission.AUTH_OWN.value, name="查看编辑本人用户信息", description="可以查看和修改自己的用户信息"),
        PermissionModel(id=Permission.BASE_EDIT.value, name="修改仓库、器材等基础数据", description="可以修改仓库、器材等基础数据信息"),
        PermissionModel(id=Permission.BASE_READ.value, name="查看仓库、器材等基础数据", description="可以查看仓库、器材等基础数据信息"),
        PermissionModel(id=Permission.IO_EDIT.value, name="出入库操作", description="可以进行出入库操作"),
        PermissionModel(id=Permission.IO_READ.value, name="查询出入库", description="可以查询出入库记录"),
        PermissionModel(id=Permission.STOCK_READ.value, name="查看库存信息", description="可以查看库存信息"),
        PermissionModel(id=Permission.SYSTEM_READ.value, name="系统设置读取", description="可以查看系统设置信息"),
        PermissionModel(id=Permission.SYSTEM_EDIT.value, name="系统设置修改", description="可以修改系统设置信息")
    ]
    
    # 添加新权限
    db.add_all(permissions)
    db.commit()
    
    # 重新获取权限，确保它们有ID
    db.refresh(permissions[0])
    
    # 获取角色，如果不存在则创建
    admin_role = db.exec(select(Role).where(Role.name == "管理员")).first()
    keeper_role = db.exec(select(Role).where(Role.name == "仓库保管员")).first()
    staff_role = db.exec(select(Role).where(Role.name == "业务部门代表")).first()
    user_role = db.exec(select(Role).where(Role.name == "普通用户")).first()
    
    # 如果角色不存在，创建它们
    if not admin_role:
        admin_role = Role(name="管理员", description="系统管理员，拥有所有权限")
        db.add(admin_role)
    
    if not keeper_role:
        keeper_role = Role(name="仓库保管员", description="负责仓库管理工作")
        db.add(keeper_role)
    
    if not staff_role:
        staff_role = Role(name="业务部门代表", description="业务部门代表，拥有部分查看权限")
        db.add(staff_role)
    
    if not user_role:
        user_role = Role(name="普通用户", description="普通用户，拥有基础权限")
        db.add(user_role)
    
    db.commit()
    db.refresh(admin_role)
    db.refresh(keeper_role)
    db.refresh(staff_role)
    db.refresh(user_role)
    
    # 创建权限映射字典，方便查找
    permission_map = {p.id: p for p in permissions}
    
    # 为每个角色分配权限
    # 管理员: 所有权限
    admin_permissions = list(permission_map.values())
    
    # 仓库保管员: AUTH-own, BASE-edit, BASE-read, IO-edit, IO-read, STOCK-read
    keeper_permissions = [
        permission_map[Permission.AUTH_OWN.value],
        permission_map[Permission.BASE_EDIT.value], permission_map[Permission.BASE_READ.value],
        permission_map[Permission.IO_EDIT.value], permission_map[Permission.IO_READ.value],
        permission_map[Permission.STOCK_READ.value]
    ]
    
    # 业务部门代表: AUTH-own, AUTH-read, BASE-read, STOCK-read
    staff_permissions = [
        permission_map[Permission.AUTH_OWN.value], permission_map[Permission.AUTH_READ.value],
        permission_map[Permission.BASE_READ.value], permission_map[Permission.STOCK_READ.value]
    ]
    
    # 普通用户: AUTH-own, STOCK-read
    user_permissions = [
        permission_map[Permission.AUTH_OWN.value], permission_map[Permission.STOCK_READ.value]
    ]
    
    # 清空现有的角色权限关联
    # 先检查表是否存在，避免查询时表不存在导致错误
    db.exec (text("DELETE FROM role_permissions"))
    db.commit()
    
    # 为每个角色创建新的权限关联
    # 管理员
    admin_role.permissions = admin_permissions
    
    # 仓库保管员
    keeper_role.permissions = keeper_permissions
    
    # 业务部门代表
    staff_role.permissions = staff_permissions
    
    # 普通用户
    user_role.permissions = user_permissions
    
    # 保存更改
    db.add_all([admin_role, keeper_role, staff_role, user_role])
    db.commit()
    
    print(f"✅ 成功创建并分配权限：")
    print(f"   - 管理员：{len(admin_permissions)} 个权限")
    print(f"   - 仓库保管员：{len(keeper_permissions)} 个权限")
    print(f"   - 业务部门代表：{len(staff_permissions)} 个权限")
    print(f"   - 普通用户：{len(user_permissions)} 个权限")
    print("🔐 权限和角色初始化完成！")


def initialize_majors(db: Session):
    """初始化专业数据"""
    print("\n📚 开始初始化专业数据...")
    
    # 定义要创建的专业数据
    majors_data = [
        # 专业名称, 专业代码
        ("船机电", "JD"),
        ("航海", "HH"),
        ("通信", "TX"),
        ("武备", "WB"),
        ("航空", "HK"),
        ("舰务", "JW"),
        ("其他", "QT")
    ]
    
    try:
        # 硬删除现有数据（完全清空表）
        db.exec(text("DELETE FROM majors"))
        db.commit()
        print("✓ 已清空专业表数据")
    except Exception as e:
        # 如果表不存在，回滚事务
        db.rollback()
        print("⚠ 专业表不存在或清空失败，将创建新表")
    
    # 创建新的专业数据
    created_count = 0
    current_time = datetime.now()
    
    for major_name, major_code in majors_data:
        # 创建新的专业记录
        major = Major(
            major_name=major_name,
            major_code=major_code,
            creator="system",
            create_time=current_time,
            update_time=current_time
        )
        db.add(major)
        created_count += 1
        print(f"✓ 创建专业: {major_name} ({major_code})")
    
    # 提交事务
    db.commit()
    
    # 验证创建结果
    total_majors = db.exec(select(Major)).all()
    
    print(f"\n🎉 专业数据初始化完成！")
    print(f"📊 总计创建: {created_count} 个专业")
    print(f"📊 当前表中专业总数: {len(total_majors)} 个")
    
    # 显示创建的专业概览
    print(f"\n📋 专业概览:")
    for major in total_majors:
        print(f"   {major.major_code} - {major.major_name}")


def get_major_id_by_name(db: Session, major_name: str) -> int:
    """根据一级专业名称获取对应的ID"""
    major = db.exec(
        select(Major).where(
            Major.major_name == major_name,
            Major.is_delete != True
        )
    ).first()
    
    if not major:
        raise ValueError(f"一级专业 '{major_name}' 不存在")
    
    return major.id


def initialize_sub_majors(db: Session):
    """初始化二级专业数据"""
    print("\n📚 开始初始化二级专业数据...")
    
    # 定义要创建的二级专业数据
    sub_majors_data = [
        # (二级专业名称, 二级专业代码, 描述, 一级专业名称)
        ("默认", "00", "[\"无法分类的\"]", "船机电"),
        ("动力装置", "DL", "", "船机电"),
        ("辅助装置", "FZ", "", "船机电"),
        ("电气设备", "DQ", "", "船机电"),
        ("默认", "00", "[\"无法分类的\"]", "航海"),
        ("默认", "00", "[\"无法分类的\"]", "通信"),
        ("默认", "00", "[\"无法分类的\"]", "武备"),
        ("默认", "00", "[\"无法分类的\"]", "航空"),
        ("默认", "00", "[\"无法分类的\"]", "舰务"),
        ("化学材料", "TL", "[\"油漆\",\"稀释剂\",\"喷漆\"]", "舰务"),
        ("除涂机具", "CT", "[\"除锈机具及配件\",\"喷涂机及配件\",\"漆刷\"]", "舰务"),
        ("清洁用品", "QJ", "[\"擦铜膏\",\"除锈剂\",\"擦机布\",\"抹布\",\"棉纱\",\"拖把\"]", "舰务"),
        ("绳网碰垫", "SW", "[\"缆绳\",\"锦纶绳\",\"碰垫\"]", "舰务"),
        ("消防救生", "XF", "[\"灭火器\",\"水龙带\",\"救生圈\",\"救生衣\",\"自亮浮灯\",\"防火服\"]", "舰务"),
        ("旗帜信号", "QZ", "[\"国旗\",\"信号旗\",\"形体信号\"]", "舰务"),
        ("默认", "00", "[\"无法分类的\"]", "其他"),
        ("办公用品", "BG", "[\"笔\",\"本\"]", "其他"),
        ("印刷制品", "YS", "[\"登记本\",\"账页\"]", "其他"),
        ("劳保用品", "LB", "[\"手套\",\"胶鞋\"]", "其他"),
        ("医疗用品", "YL", "[\"口罩\",\"防护服\",\"喷雾机\"]", "其他")
    ]
    
    try:
        # 硬删除现有数据（完全清空表）
        db.exec(text("DELETE FROM sub_majors"))
        db.commit()
        print("✓ 已清空二级专业表数据")
    except Exception as e:
        # 如果表不存在，回滚事务
        db.rollback()
        print("⚠ 二级专业表不存在或清空失败，将创建新表")
    
    # 创建新的二级专业数据
    created_count = 0
    current_time = datetime.now()
    
    for sub_major_name, sub_major_code, description, major_name in sub_majors_data:
        try:
            # 根据一级专业名称获取ID
            major_id = get_major_id_by_name(db, major_name)
            
            # 创建新的二级专业记录
            sub_major = SubMajor(
                sub_major_name=sub_major_name,
                sub_major_code=sub_major_code,
                description=description if description else None,
                major_id=major_id,
                major_name=major_name,  # 通过major_id自动获取
                reserved=None,  # 保留字段，不要求输入
                creator="system",
                create_time=current_time,
                update_time=current_time
            )
            db.add(sub_major)
            created_count += 1
            print(f"✓ 创建二级专业: {sub_major_name} ({sub_major_code}) - 所属一级专业: {major_name}")
            
        except ValueError as e:
            print(f"✗ 创建失败: {sub_major_name} ({sub_major_code}) - {e}")
        except Exception as e:
            print(f"✗ 创建失败: {sub_major_name} ({sub_major_code}) - 错误: {e}")
    
    # 提交事务
    db.commit()
    
    # 验证创建结果
    total_sub_majors = db.exec(select(SubMajor)).all()
    
    print(f"\n🎉 二级专业数据初始化完成！")
    print(f"📊 总计创建: {created_count} 个二级专业")
    print(f"📊 当前表中二级专业总数: {len(total_sub_majors)} 个")
    
    # 显示创建的二级专业概览（按一级专业分组）
    print(f"\n📋 二级专业概览（按一级专业分组）:")
    
    # 按一级专业名称分组显示
    major_groups = {}
    for sub_major in total_sub_majors:
        major_name = sub_major.major_name or "未分类"
        if major_name not in major_groups:
            major_groups[major_name] = []
        major_groups[major_name].append(sub_major)
    
    for major_name, sub_majors in major_groups.items():
        print(f"\n   📍 一级专业: {major_name}")
        for sub_major in sub_majors:
            desc = sub_major.description or "无描述"
            print(f"      {sub_major.sub_major_code} - {sub_major.sub_major_name} ({desc})")


def initialize_equipments(db: Session):
    """初始化装备数据"""
    print("\n🔧 开始初始化装备数据...")
    
    try:
        # 硬删除现有数据（完全清空表）
        db.exec(text("DELETE FROM equipments"))
        db.commit()
        print("✓ 已清空装备表数据")
    except Exception as e:
        # 如果表不存在，回滚事务
        db.rollback()
        print("⚠ 装备表不存在或清空失败，将创建新表")
    
    # 获取所有一级专业（在清空操作之后获取）
    majors = db.exec(select(Major)).all()
    
    if not majors:
        print("⚠ 没有找到一级专业数据，请先初始化专业数据")
        return
    
    # 创建新的装备数据
    created_count = 0
    current_time = datetime.now()
    
    for major in majors:
        # 为每个一级专业创建一个"通用"装备
        equipment = Equipment(
            equipment_name=f"{major.major_name}通用装备",
            equipment_code=f"{major.major_code}_TY",
            description=f"{major.major_name}专业通用装备",
            major_id=major.id,
            major_name=major.major_name,
            sub_major_id=None,  # 不关联二级专业
            sub_major_name=None,
            reserved=None,  # 保留字段
            creator="system",
            create_time=current_time,
            update_time=current_time
        )
        db.add(equipment)
        created_count += 1
        print(f"✓ 创建装备: {equipment.equipment_name} ({equipment.equipment_code}) - 所属专业: {major.major_name}")
    
    # 提交事务
    db.commit()
    
    # 验证创建结果
    total_equipments = db.exec(select(Equipment)).all()
    
    print(f"\n🎉 装备数据初始化完成！")
    print(f"📊 总计创建: {created_count} 个装备")
    print(f"📊 当前表中装备总数: {len(total_equipments)} 个")
    
    # 显示创建的装备概览
    print(f"\n📋 装备概览:")
    for equipment in total_equipments:
        print(f"   {equipment.equipment_code} - {equipment.equipment_name} (所属专业: {equipment.major_name})")


def initialize_material_code_levels(db: Session):
    """初始化器材编码分类层级数据"""
    print("\n🏷️ 开始初始化器材编码分类层级数据...")
    
    try:
        # 硬删除现有数据（完全清空表）
        db.exec(text("DELETE FROM material_code_levels"))
        db.commit()
        print("✓ 已清空器材编码分类层级表数据")
    except Exception as e:
        # 如果表不存在，回滚事务
        db.rollback()
        print("⚠ 器材编码分类层级表不存在或清空失败，将创建新表")
    # 定义要创建的器材编码分类层级数据
    material_code_levels = [
        # 层级编码, 层级名称, 专业代码, 描述列表
        ("1", "船机电", "JD", ["船机电专业"]),
        ("1-0", "默认", "00", ["无法分类的"]),
        ("1-1", "动力装置", "DL", []),
        ("1-2", "辅助装置", "FZ", []),
        ("1-3", "电气设备", "DQ", []),
        ("2", "航海", "HH", []),
        ("2-0", "默认", "00", ["无法分类的"]),
        ("3", "通信", "TX", []),
        ("3-0", "默认", "00", ["无法分类的"]),
        ("4", "武备", "WB", []),
        ("4-0", "默认", "00", ["无法分类的"]),
        ("5", "航空", "HK", []),
        ("5-0", "默认", "00", ["无法分类的"]),
        ("6", "舰务", "JW", []),
        ("6-0", "默认", "00", ["无法分类的"]),
        ("6-1", "化学材料", "TL", ["油漆", "稀释剂", "喷漆"]),
        ("6-2", "除涂机具", "CT", ["除锈机具及配件", "喷涂机及配件", "漆刷"]),
        ("6-3", "清洁用品", "QJ", ["擦铜膏", "除锈剂", "擦机布", "抹布", "棉纱", "拖把"]),
        ("6-4", "绳网碰垫", "SW", ["缆绳", "锦纶绳", "碰垫"]),
        ("6-5", "消防器材", "XF", ["灭火器", "消防栓", "消防水带"]),
        ("6-6", "救生器材", "JS", ["救生圈", "救生衣", "救生筏"]),
        ("6-7", "堵漏器材", "DL", ["堵漏毯", "堵漏箱", "堵漏板"]),
        ("6-8", "信号器材", "XH", ["信号旗", "信号灯", "信号弹"]),
        ("6-9", "航海图书", "HT", ["海图", "航海日志", "航海手册"]),
        ("6-10", "医疗器材", "YL", ["急救箱", "药品", "医疗器械"]),
        ("6-11", "办公用品", "BG", ["纸张", "笔", "文件夹"]),
        ("6-12", "生活用品", "SH", ["餐具", "洗漱用品", "床上用品"])
    ]
    
    # 创建新的器材编码分类层级数据
    created_count = 0
    
    for level_code, level_name, code, description_list in material_code_levels:
        try:
            # 将描述列表转换为JSON字符串
            import json
            description_json = json.dumps(description_list, ensure_ascii=False) if description_list else None
            
            material_code_level = MaterialCodeLevel(
                level_code=level_code,
                level_name=level_name,
                code=code,
                description=description_json
            )
            db.add(material_code_level)
            created_count += 1
            
            # 显示描述信息
            desc_info = f"描述: {description_list}" if description_list else "无描述"
            print(f"✓ 创建器材编码分类层级: {level_code} - {level_name} ({code}) - {desc_info}")
            
        except Exception as e:
            print(f"✗ 创建失败: {level_code} - {level_name} ({code}) - 错误: {e}")
    
    # 提交事务
    db.commit()
    
    # 验证创建结果
    total_levels = db.exec(select(MaterialCodeLevel)).all()
    
    print(f"\n🎉 器材编码分类层级数据初始化完成！")
    print(f"📊 总计创建: {created_count} 个器材编码分类层级")
    print(f"📊 当前表中器材编码分类层级总数: {len(total_levels)} 个")
    
    # 显示创建的器材编码分类层级概览（按层级深度分组）
    print(f"\n📋 器材编码分类层级概览（按层级深度分组）:")
    
    # 按层级深度分组显示
    level_groups = {}
    for level in total_levels:
        depth = len(level.level_code.split('-'))
        if depth not in level_groups:
            level_groups[depth] = []
        level_groups[depth].append(level)
    
    for depth, levels in sorted(level_groups.items()):
        print(f"\n   📍 层级深度 {depth}:")
        for level in levels:
            desc = level.description or "无描述"
            print(f"      {level.level_code} - {level.level_name} ({level.code}) - {desc}")


def initialize_users(db: Session):
    """初始化用户数据 - 清除所有用户并生成admin用户"""
    print("\n👤 开始初始化用户数据...")
    
    # 导入密码加密函数
    from core.security import get_password_hash
    from models.account.user import User
    
    try:
        # 清除所有用户数据（硬删除）
        db.exec(text("DELETE FROM users"))
        print("✓ 已清空用户表数据")
    except Exception as e:
        # 如果表不存在，回滚事务
        db.rollback()
        print("⚠ 用户表不存在或清空失败，将创建新表")    
    # 获取管理员角色ID
    admin_role = db.exec(select(Role).where(Role.name == "管理员")).first()
    if not admin_role:
        print("❌ 管理员角色不存在，请先初始化权限和角色")
        return
    
    # 创建admin用户
    try:
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin"),  # 使用加密密码
            role_id=admin_role.id,
            department="系统管理部",
            avatar="XX/user.jpg"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✓ 创建管理员用户: admin (密码: admin)")
        print(f"✓ 用户角色: 管理员")
        print(f"✓ 所属单位: 系统管理部")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建管理员用户失败: {e}")
        raise
    
    print("✅ 用户数据初始化完成！")


def initialize_warehouse(db: Session):
    """初始化仓库数据 - 创建默认仓库"""
    print("\n🏭 开始初始化仓库数据...")
    
    from models.base.warehouse import Warehouse
    
    try:
        # 清除所有仓库数据（硬删除）
        db.exec(text("DELETE FROM warehouses"))
        print("✓ 已清空仓库表数据")
    except Exception as e:
        # 如果表不存在，回滚事务
        db.rollback()
        print("⚠ 仓库表不存在或清空失败，将创建新表")
    
    # 创建默认仓库
    try:
        warehouse = Warehouse(
            warehouse_name="1号仓库",
            warehouse_address="默认地址",
            warehouse_manager="管理员",
            warehouse_contact="默认联系方式",
            creator="system"
        )
        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)
        
        print(f"✓ 创建默认仓库: 1号仓库")
        print(f"✓ 仓库地址: 默认地址")
        print(f"✓ 仓库管理员: 管理员")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建默认仓库失败: {e}")
        raise
    
    print("✅ 仓库数据初始化完成！")


def initialize_bin(db: Session):
    """初始化货位数据 - 创建默认货位"""
    print("\n📦 开始初始化货位数据...")
    
    from models.base.bin import Bin
    from models.base.warehouse import Warehouse
    
    try:
        # 清除所有货位数据（硬删除）
        db.exec(text("DELETE FROM bins"))
        print("✓ 已清空货位表数据")
    except Exception as e:
        # 如果表不存在，回滚事务
        db.rollback()
        print("⚠ 货位表不存在或清空失败，将创建新表")
    
    # 获取默认仓库
    warehouse = db.exec(select(Warehouse).where(Warehouse.warehouse_name == "1号仓库")).first()
    if not warehouse:
        print("❌ 默认仓库不存在，请先初始化仓库数据")
        return
    
    # 创建默认货位
    try:
        bin = Bin(
            bin_name="默认货位",
            bin_size="默认尺寸",
            bin_property="周转区",
            warehouse_id=warehouse.id,
            warehouse_name=warehouse.warehouse_name,
            creator="system"
        )
        db.add(bin)
        db.commit()
        db.refresh(bin)
        
        print(f"✓ 创建默认货位: 默认货位")
        print(f"✓ 货位属性: 周转区")
        print(f"✓ 所属仓库: {warehouse.warehouse_name}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建默认货位失败: {e}")
        raise
    
    print("✅ 货位数据初始化完成！")


def initialize_all():
    """执行完整的系统初始化（包括配置、权限、角色、专业、二级专业、装备数据和器材编码分类层级数据）"""
    print("🚀 开始完整系统初始化...")
    # 初始化系统配置
    initialize_system_config()

    # 初始化主数据库（如果未初始化）
    initialize_main_db()


def initialize_main_db():
    """初始化主数据库"""
    print("\n🔍 检查主数据库初始化状态...")
    
    # 检查主数据库的初始化状态
    main_db_initialized = is_main_db_initialized()
    
    print(f"📊 主数据库初始化状态: {'已初始化' if main_db_initialized else '未初始化'}")
    
    # 如果主数据库已初始化，则跳过
    if main_db_initialized:
        print("⚠ 主数据库已初始化，跳过主数据库初始化")
        return
    
    # 初始化主数据库（如果未初始化）
    if not main_db_initialized:
        print("\n🗄️ 开始初始化主数据库...")
        
        # 连接主数据库
        from database import get_engine
        engine = get_engine()
        with Session(engine) as db:
            try:
                # 确保表存在 - 使用database.py中的init_db函数
                from database import init_db
                init_db()
                #初始化生成默认仓库
                initialize_warehouse(db)
                #初始化生成默认货位
                initialize_bin(db)
                # 初始化权限和角色
                initialize_permissions_and_roles(db)
                # 初始化用户
                initialize_users(db)
                
                # 初始化专业数据
                initialize_majors(db)
                
                # 初始化二级专业数据
                initialize_sub_majors(db)
                
                # 初始化装备数据
                initialize_equipments(db)
                
                # 初始化器材编码分类层级数据
                initialize_material_code_levels(db)
                
                # 创建主数据库初始化记录
                init_record = SystemInit(
                    initialized=True,
                    init_time=datetime.now(),
                    init_version="1.0.0"
                )
                db.add(init_record)
                
                # 提交事务
                db.commit()
                
                print(f"✅ 主数据库初始化完成！")
                print(f"📊 初始化时间: {datetime.now()}")
                
            except Exception as e:
                db.rollback()
                print(f"❌ 主数据库初始化失败: {e}")
                raise
    
    print(f"\n🎉 完整系统初始化完成！")
    print(f"📊 完成时间: {datetime.now()}")


if __name__ == "__main__":
    initialize_all()