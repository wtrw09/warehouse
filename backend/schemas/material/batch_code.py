from pydantic import BaseModel, Field
from datetime import date


class BatchCodeGenerateRequest(BaseModel):
    """批次编码生成请求模型"""
    material_id: int = Field(..., description="器材ID")
    batch_date: date = Field(..., description="日期")


class BatchCodeGenerateResponse(BaseModel):
    """批次编码生成响应模型"""
    batch_code: str = Field(..., description="生成的批次编码")
    material_code: str = Field(..., description="器材编码")
    batch_date: date = Field(..., description="日期")
    sequence: int = Field(..., description="流水号")