from typing import Dict, Optional
from schemas.common.import_schemas import ImportConfig, TemplateField, ValidationRule, PreviewColumn

def get_supplier_import_config() -> ImportConfig:
    """获取供应商导入配置"""
    return ImportConfig(
        entity_name="供应商",
        entity_key="supplier",
        template_fields=[
            TemplateField(
                key="supplier_name",
                label="供应商名称",
                required=True,
                type="string",
                max_length=100,
                example="北京科技有限公司"
            ),
            TemplateField(
                key="supplier_city",
                label="所在城市",
                required=False,
                type="string",
                max_length=50,
                example="北京"
            ),
            TemplateField(
                key="supplier_address",
                label="详细地址",
                required=False,
                type="string",
                max_length=200,
                example="朝阳区xxx街道"
            ),
            TemplateField(
                key="supplier_manager",
                label="负责人",
                required=False,
                type="string",
                max_length=50,
                example="张三"
            ),
            TemplateField(
                key="supplier_contact",
                label="联系方式",
                required=False,
                type="string",
                max_length=50,
                example="13800138000"
            ),
            TemplateField(
                key="supplier_level",
                label="供应商等级",
                required=False,
                type="integer",
                example="1"
            )
        ],
        validation_rules=[
            ValidationRule(
                field="supplier_name",
                type="required",
                message="供应商:供应商名称:不能为空"
            ),
            ValidationRule(
                field="supplier_name",
                type="max_length",
                value=100,
                message="供应商:供应商名称:长度不能超过100个字符"
            ),
            ValidationRule(
                field="supplier_name",
                type="unique",
                message="供应商:供应商名称:已存在"
            ),
            ValidationRule(
                field="supplier_city",
                type="max_length",
                value=50,
                message="供应商:所在城市:长度不能超过50个字符"
            ),
            ValidationRule(
                field="supplier_address",
                type="max_length",
                value=200,
                message="供应商:详细地址:长度不能超过200个字符"
            ),
            ValidationRule(
                field="supplier_manager",
                type="max_length",
                value=50,
                message="供应商:负责人:长度不能超过50个字符"
            ),
            ValidationRule(
                field="supplier_contact",
                type="max_length",
                value=50,
                message="供应商:联系方式:长度不能超过50个字符"
            ),
            ValidationRule(
                field="supplier_level",
                type="range",
                value=5,
                message="供应商:供应商等级:必须是1-5的整数"
            )
        ],
        unique_fields=["supplier_name"],
        preview_columns=[
            PreviewColumn(key="supplier_name", label="供应商名称", width=150),
            PreviewColumn(key="supplier_city", label="所在城市", width=100),
            PreviewColumn(key="supplier_address", label="详细地址", width=200),
            PreviewColumn(key="supplier_manager", label="负责人", width=100),
            PreviewColumn(key="supplier_contact", label="联系方式", width=120),
            PreviewColumn(key="supplier_level", label="供应商等级", width=100)
        ]
    )

def get_customer_import_config() -> ImportConfig:
    """获取客户导入配置"""
    return ImportConfig(
        entity_name="客户",
        entity_key="customer",
        template_fields=[
            TemplateField(
                key="customer_name",
                label="单位名称",
                required=True,
                type="string",
                max_length=100,
                example="北京科技有限公司"
            ),
            TemplateField(
                key="customer_city",
                label="所在城市",
                required=False,
                type="string",
                max_length=50,
                example="北京"
            ),
            TemplateField(
                key="customer_address",
                label="地址",
                required=False,
                type="string",
                max_length=200,
                example="朝阳区xxx街道"
            ),
            TemplateField(
                key="customer_contact",
                label="联系方式",
                required=False,
                type="string",
                max_length=50,
                example="13800138000"
            ),
            TemplateField(
                key="customer_manager",
                label="负责人",
                required=False,
                type="string",
                max_length=50,
                example="张三"
            ),
        ],
        validation_rules=[
            ValidationRule(
                field="customer_name",
                type="required",
                message="客户:单位名称:不能为空"
            ),
            ValidationRule(
                field="customer_name",
                type="max_length",
                value=100,
                message="客户:单位名称:长度不能超过100个字符"
            ),
            ValidationRule(
                field="customer_name",
                type="unique",
                message="客户:单位名称:已存在"
            ),
            ValidationRule(
                field="customer_city",
                type="max_length",
                value=50,
                message="客户:所在城市:长度不能超过50个字符"
            ),
            ValidationRule(
                field="customer_address",
                type="max_length",
                value=200,
                message="客户:地址:长度不能超过200个字符"
            ),
            ValidationRule(
                field="customer_contact",
                type="max_length",
                value=50,
                message="客户:联系方式:长度不能超过50个字符"
            ),
            ValidationRule(
                field="customer_manager",
                type="max_length",
                value=50,
                message="客户:负责人:长度不能超过50个字符"
            ),
        ],
        unique_fields=["customer_name"],
        preview_columns=[
            PreviewColumn(key="customer_name", label="单位名称", width=150),
            PreviewColumn(key="customer_city", label="所在城市", width=100),
            PreviewColumn(key="customer_address", label="地址", width=200),
            PreviewColumn(key="customer_contact", label="联系方式", width=120),
            PreviewColumn(key="customer_manager", label="负责人", width=100),
        ]
    )

def get_warehouse_import_config() -> ImportConfig:
    """获取仓库导入配置"""
    return ImportConfig(
        entity_name="仓库",
        entity_key="warehouse",
        template_fields=[
            TemplateField(
                key="warehouse_name",
                label="仓库名",
                required=True,
                type="string",
                max_length=100,
                example="北京仓库"
            ),
            TemplateField(
                key="warehouse_city",
                label="所在城市",
                required=False,
                type="string",
                max_length=50,
                example="北京"
            ),
            TemplateField(
                key="warehouse_address",
                label="地址",
                required=False,
                type="string",
                max_length=200,
                example="朝阳区xxx街道"
            ),
            TemplateField(
                key="warehouse_manager",
                label="负责人",
                required=False,
                type="string",
                max_length=50,
                example="张三"
            ),
            TemplateField(
                key="warehouse_contact",
                label="联系方式",
                required=False,
                type="string",
                max_length=50,
                example="13800138000"
            ),
        ],
        validation_rules=[
            ValidationRule(
                field="warehouse_name",
                type="required",
                message="仓库:仓库名:不能为空"
            ),
            ValidationRule(
                field="warehouse_name",
                type="max_length",
                value=100,
                message="仓库:仓库名:长度不能超过100个字符"
            ),
            ValidationRule(
                field="warehouse_name",
                type="unique",
                message="仓库:仓库名:已存在"
            ),
            ValidationRule(
                field="warehouse_city",
                type="max_length",
                value=50,
                message="仓库:所在城市:长度不能超过50个字符"
            ),
            ValidationRule(
                field="warehouse_address",
                type="max_length",
                value=200,
                message="仓库:地址:长度不能超过200个字符"
            ),
            ValidationRule(
                field="warehouse_contact",
                type="max_length",
                value=50,
                message="仓库:联系方式:长度不能超过50个字符"
            ),
            ValidationRule(
                field="warehouse_manager",
                type="max_length",
                value=50,
                message="仓库:负责人:长度不能超过50个字符"
            ),
        ],
        unique_fields=["warehouse_name"],
        preview_columns=[
            PreviewColumn(key="warehouse_name", label="仓库名", width=150),
            PreviewColumn(key="warehouse_city", label="所在城市", width=100),
            PreviewColumn(key="warehouse_address", label="地址", width=200),
            PreviewColumn(key="warehouse_contact", label="联系方式", width=120),
            PreviewColumn(key="warehouse_manager", label="负责人", width=100),
        ]
    )

def get_material_import_config() -> ImportConfig:
    """获取器材导入配置"""
    return ImportConfig(
        entity_name="器材",
        entity_key="material",
        template_fields=[
            TemplateField(
                key="material_code",
                label="器材编码",
                required=True,
                type="string",
                max_length=50,
                example="MAT001"
            ),
            TemplateField(
                key="material_name",
                label="器材名称",
                required=True,
                type="string",
                max_length=100,
                example="螺丝刀"
            ),
            TemplateField(
                key="material_specification",
                label="器材规格",
                required=False,
                type="string",
                max_length=200,
                example="十字型，长度20cm"
            ),
            TemplateField(
                key="material_desc",
                label="器材描述",
                required=False,
                type="string",
                max_length=500,
                example="用于拧十字螺丝的工具"
            ),
            TemplateField(
                key="material_wdh",
                label="器材尺寸",
                required=False,
                type="string",
                max_length=50,
                example="20x5x3cm"
            ),
            TemplateField(
                key="safety_stock",
                label="安全库存",
                required=False,
                type="integer",
                example="100"
            ),
            TemplateField(
                key="material_query_code",
                label="器材查询码",
                required=False,
                type="string",
                max_length=100,
                example="LSDSX20"
            )
        ],
        validation_rules=[
            ValidationRule(
                field="material_code",
                type="required",
                message="器材:器材编码:不能为空"
            ),
            ValidationRule(
                field="material_code",
                type="max_length",
                value=50,
                message="器材:器材编码:长度不能超过50个字符"
            ),
            ValidationRule(
                field="material_code",
                type="unique",
                message="器材:器材编码:已存在"
            ),
            ValidationRule(
                field="material_name",
                type="required",
                message="器材:器材名称:不能为空"
            ),
            ValidationRule(
                field="material_name",
                type="max_length",
                value=100,
                message="器材:器材名称:长度不能超过100个字符"
            ),
            ValidationRule(
                field="material_specification",
                type="max_length",
                value=200,
                message="器材:器材规格:长度不能超过200个字符"
            ),
            ValidationRule(
                field="material_desc",
                type="max_length",
                value=500,
                message="器材:器材描述:长度不能超过500个字符"
            ),
            ValidationRule(
                field="material_wdh",
                type="max_length",
                value=50,
                message="器材:器材尺寸:长度不能超过50个字符"
            ),
            ValidationRule(
                field="safety_stock",
                type="min",
                value=0,
                message="器材:安全库存:必须大于等于0"
            ),
            ValidationRule(
                field="material_query_code",
                type="max_length",
                value=100,
                message="器材:器材查询码:长度不能超过100个字符"
            )
        ],
        unique_fields=["material_code"],
        preview_columns=[
            PreviewColumn(key="material_code", label="器材编码", width=120),
            PreviewColumn(key="material_name", label="器材名称", width=150),
            PreviewColumn(key="material_specification", label="器材规格", width=200),
            PreviewColumn(key="material_desc", label="器材描述", width=200),
            PreviewColumn(key="material_wdh", label="器材尺寸", width=120),
            PreviewColumn(key="safety_stock", label="安全库存", width=100),
            PreviewColumn(key="material_query_code", label="器材查询码", width=120)
        ]
    )

def get_import_config(entity_type: str) -> Optional[ImportConfig]:
    """根据实体类型获取导入配置"""
    configs = {
        'supplier': get_supplier_import_config,
        'customer': get_customer_import_config,
        'warehouse': get_warehouse_import_config,
        'material': get_material_import_config,
        # 后续可以添加其他实体的配置
        # 'bin': get_bin_import_config,
    }
    
    config_func = configs.get(entity_type)
    return config_func() if config_func else None