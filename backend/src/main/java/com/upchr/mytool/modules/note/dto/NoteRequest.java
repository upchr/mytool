package com.upchr.mytool.modules.note.dto;

import lombok.Data;

import java.util.List;

/**
 * 批量删除请求
 */
@Data
public class NoteRequest {
    private List<Long> noteIds;
}
