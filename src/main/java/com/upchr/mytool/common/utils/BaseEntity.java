package com.upchr.mytool.common.utils;

import cn.hutool.core.util.StrUtil;

/**
 * 基础实体类
 */
public interface BaseEntity {

    /**
     * 获取 ID
     */
    Long getId();

    /**
     * 设置 ID
     */
    void setId(Long id);
}
