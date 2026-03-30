package com.upchr.mytool.modules.note.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 便签实体
 */
@Data
@TableName("notes")
public class Note {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;

    private String content;
}
