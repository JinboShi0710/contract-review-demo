# -*- coding: utf-8 -*-
"""
审核点配置服务
提供配置的 CRUD 操作和版本管理
"""
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.audit_rule import (
    AuditRule,
    AuditRuleVersion,
    DEFAULT_AUDIT_RULES,
)


class AuditRuleService:
    """审核点配置服务"""

    # 用户自定义规则上限
    USER_RULE_LIMIT = 50

    # 版本历史保留数量
    VERSION_LIMIT = 30

    def __init__(self):
        pass

    # ========== 配置查询 ==========

    def list_rules(
        self,
        db: Session,
        include_deleted: bool = False,
        global_only: bool = False,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """获取配置列表"""
        query = db.query(AuditRule)

        if not include_deleted:
            query = query.filter(AuditRule.is_deleted == 0)

        if global_only:
            query = query.filter(AuditRule.is_global == True)

        if user_id:
            query = query.filter(
                (AuditRule.is_global == False) & (AuditRule.created_by == user_id)
            )

        rules = query.order_by(desc(AuditRule.created_at)).all()

        return [self._rule_to_dict(r) for r in rules]

    def get_rule(self, db: Session, rule_id: str) -> Optional[Dict]:
        """获取单个配置"""
        rule = db.query(AuditRule).filter(
            AuditRule.id == rule_id,
            AuditRule.is_deleted == 0,
        ).first()

        return self._rule_to_dict(rule) if rule else None

    def get_enabled_rules(self, db: Session, user_id: Optional[str] = None) -> List[Dict]:
        """获取已启用的配置（全局 + 用户自定义）"""
        rules = db.query(AuditRule).filter(
            AuditRule.is_deleted == 0,
            AuditRule.enabled == True,
        ).all()

        # 如果指定了用户，合并全局和用户的配置
        if user_id:
            rules = [
                r for r in rules
                if r.is_global or r.created_by == user_id
            ]

        return [self._rule_to_dict(r) for r in rules]

    # ========== 配置创建 ==========

    def create_rule(
        self,
        db: Session,
        name: str,
        rule_type: str,
        params: Dict,
        severity: str,
        description: Optional[str],
        is_global: bool,
        created_by: str,
    ) -> Dict:
        """创建配置"""
        # 检查用户规则数量限制
        if not is_global:
            user_count = db.query(AuditRule).filter(
                AuditRule.created_by == created_by,
                AuditRule.is_global == False,
                AuditRule.is_deleted == 0,
            ).count()

            if user_count >= self.USER_RULE_LIMIT:
                raise ValueError(f"用户自定义规则已达上限（{self.USER_RULE_LIMIT}个）")

        rule = AuditRule(
            id=str(uuid.uuid4()),
            name=name,
            rule_type=rule_type,
            params=params,
            severity=severity,
            description=description,
            is_global=is_global,
            created_by=created_by,
            enabled=True,
        )
        db.add(rule)

        # 创建初始版本
        self._create_version(db, rule, "create", created_by)

        db.commit()
        db.refresh(rule)

        return self._rule_to_dict(rule)

    # ========== 配置修改 ==========

    def update_rule(
        self,
        db: Session,
        rule_id: str,
        name: Optional[str] = None,
        params: Optional[Dict] = None,
        severity: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[Dict]:
        """修改配置"""
        rule = db.query(AuditRule).filter(
            AuditRule.id == rule_id,
            AuditRule.is_deleted == 0,
        ).first()

        if not rule:
            return None

        # 普通用户不能修改全局配置
        if rule.is_global and updated_by != "admin":
            raise PermissionError("普通用户不能修改全局配置")

        if name is not None:
            rule.name = name
        if params is not None:
            rule.params = params
        if severity is not None:
            rule.severity = severity
        if description is not None:
            rule.description = description
        if enabled is not None:
            rule.enabled = enabled

        # 创建版本记录
        self._create_version(db, rule, "update", updated_by or rule.created_by)

        db.commit()
        db.refresh(rule)

        return self._rule_to_dict(rule)

    # ========== 配置删除 ==========

    def delete_rule(self, db: Session, rule_id: str, deleted_by: str) -> bool:
        """删除配置（软删除）"""
        rule = db.query(AuditRule).filter(
            AuditRule.id == rule_id,
            AuditRule.is_deleted == 0,
        ).first()

        if not rule:
            return False

        # 普通用户不能删除全局配置
        if rule.is_global and deleted_by != "admin":
            raise PermissionError("普通用户不能删除全局配置")

        # 普通用户不能删除别人的配置
        if not rule.is_global and rule.created_by != deleted_by and deleted_by != "admin":
            raise PermissionError("不能删除其他用户的配置")

        rule.is_deleted = 1

        # 创建版本记录
        self._create_version(db, rule, "delete", deleted_by)

        db.commit()
        return True

    # ========== 版本管理 ==========

    def list_versions(self, db: Session, rule_id: str) -> List[Dict]:
        """获取版本历史"""
        versions = db.query(AuditRuleVersion).filter(
            AuditRuleVersion.rule_id == rule_id,
        ).order_by(desc(AuditRuleVersion.version)).limit(self.VERSION_LIMIT).all()

        return [self._version_to_dict(v) for v in versions]

    def rollback(
        self,
        db: Session,
        rule_id: str,
        target_version: int,
        rolled_back_by: str,
    ) -> Optional[Dict]:
        """回滚到指定版本"""
        version = db.query(AuditRuleVersion).filter(
            AuditRuleVersion.rule_id == rule_id,
            AuditRuleVersion.version == target_version,
        ).first()

        if not version:
            return None

        rule = db.query(AuditRule).filter(
            AuditRule.id == rule_id,
            AuditRule.is_deleted == 0,
        ).first()

        if not rule:
            return None

        # 恢复配置
        rule.name = version.name
        rule.description = version.description
        rule.rule_type = version.rule_type
        rule.params = version.params
        rule.severity = version.severity

        # 创建新的版本记录
        self._create_version(db, rule, "rollback", rolled_back_by)

        db.commit()
        db.refresh(rule)

        return self._rule_to_dict(rule)

    # ========== 配置导入 ==========

    def import_default_rules(self, db: Session, admin_user: str = "system") -> int:
        """导入默认规则（从硬编码配置）"""
        count = 0
        for rule_config in DEFAULT_AUDIT_RULES:
            # 检查是否已存在
            existing = db.query(AuditRule).filter(
                AuditRule.name == rule_config["name"],
                AuditRule.is_global == True,
                AuditRule.is_deleted == 0,
            ).first()

            if not existing:
                rule = AuditRule(
                    id=str(uuid.uuid4()),
                    name=rule_config["name"],
                    description=rule_config["description"],
                    rule_type=rule_config["rule_type"],
                    params=rule_config["params"],
                    severity=rule_config["severity"],
                    is_global=True,
                    created_by=admin_user,
                    enabled=True,
                )
                db.add(rule)
                count += 1

        if count > 0:
            db.commit()

        return count

    # ========== 私有方法 ==========

    def _create_version(
        self,
        db: Session,
        rule: AuditRule,
        change_type: str,
        changed_by: str,
    ) -> None:
        """创建版本记录"""
        # 获取当前最大版本号
        max_version = db.query(AuditRuleVersion).filter(
            AuditRuleVersion.rule_id == rule.id,
        ).count()

        version = AuditRuleVersion(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            version=max_version + 1,
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type,
            params=rule.params,
            severity=rule.severity,
            change_type=change_type,
            changed_by=changed_by,
        )
        db.add(version)

        # 清理旧版本（保留最近 VERSION_LIMIT 个）
        old_versions = db.query(AuditRuleVersion).filter(
            AuditRuleVersion.rule_id == rule.id,
        ).order_by(desc(AuditRuleVersion.version)).all()

        if len(old_versions) > self.VERSION_LIMIT:
            for v in old_versions[self.VERSION_LIMIT:]:
                db.delete(v)

    def _rule_to_dict(self, rule: AuditRule) -> Dict:
        """转换规则为字典"""
        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "rule_type": rule.rule_type,
            "enabled": rule.enabled,
            "params": rule.params,
            "severity": rule.severity,
            "is_global": rule.is_global,
            "created_by": rule.created_by,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
            "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        }

    def _version_to_dict(self, version: AuditRuleVersion) -> Dict:
        """转换版本为字典"""
        return {
            "id": version.id,
            "rule_id": version.rule_id,
            "version": version.version,
            "name": version.name,
            "description": version.description,
            "rule_type": version.rule_type,
            "params": version.params,
            "severity": version.severity,
            "change_type": version.change_type,
            "changed_by": version.changed_by,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }


# 单例
audit_rule_service = AuditRuleService()
