-- PostgreSQL数据库初始化脚本
-- 医疗AI平台数据库设置

-- 创建数据库
CREATE DATABASE medical_ai_db;

-- 创建用户
CREATE USER medical_ai_user WITH PASSWORD '259006';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE medical_ai_db TO medical_ai_user;

-- 连接到数据库
\c medical_ai_db;

-- 授予schema权限
GRANT ALL ON SCHEMA public TO medical_ai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medical_ai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO medical_ai_user;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO medical_ai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO medical_ai_user;

-- 为prediction_records表添加risk_level字段
-- 执行此脚本前请确保已备份数据库

-- 1. 添加risk_level字段
ALTER TABLE prediction_records 
ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20);

-- 2. 为risk_level字段添加注释
COMMENT ON COLUMN prediction_records.risk_level IS '风险等级: high, medium, low, info';

-- 3. 查看表结构确认字段已添加
\d prediction_records;

-- 4. 查看当前记录数量
SELECT COUNT(*) as total_records FROM prediction_records;

-- 5. 查看各模型类型的记录数量
SELECT 
    model_type,
    COUNT(*) as count
FROM prediction_records 
GROUP BY model_type 
ORDER BY count DESC; 