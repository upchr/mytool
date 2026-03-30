package com.upchr.mytool.modules.note.controller;

import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.common.result.BaseResponse;
import com.upchr.mytool.modules.note.dto.NoteRequest;
import com.upchr.mytool.modules.note.entity.Note;
import com.upchr.mytool.modules.note.service.NoteService;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 便签控制器
 */
@Tag(name = "便签管理")
@RestController
@RequestMapping("/notes")
@RequiredArgsConstructor
public class NoteController {

    private final NoteService noteService;

    @GetMapping
    public BaseResponse<?> list() {
        return BaseResponse.success(noteService.getAllNotes());
    }

    @PostMapping
    public BaseResponse<Note> create(@RequestBody Note note) {
        return BaseResponse.success(noteService.createNote(note));
    }

    @PutMapping("/{id}")
    public BaseResponse<Note> update(@PathVariable Long id, @RequestBody Note note) {
        Note updated = noteService.updateNote(id, note);
        if (updated == null) {
            throw new BusinessException("便签不存在");
        }
        return BaseResponse.success(updated);
    }

    @DeleteMapping("/{id}")
    public BaseResponse<Map<String, Object>> delete(@PathVariable Long id) {
        boolean success = noteService.deleteNote(id);
        if (!success) {
            throw new BusinessException("便签不存在");
        }
        Map<String, Object> data = new HashMap<>();
        data.put("status", "ok");
        data.put("id", id);
        return BaseResponse.success(data);
    }

    @PostMapping("/deleteBatch")
    public BaseResponse<Void> batchDelete(@RequestBody NoteRequest request) {
        if (request.getNoteIds() == null || request.getNoteIds().isEmpty()) {
            throw new BusinessException("便签ID列表不能为空");
        }
        noteService.batchDelete(request.getNoteIds());
        return BaseResponse.success();
    }

    @GetMapping("/{title}")
    public BaseResponse<Note> getByTitle(@PathVariable String title) {
        return BaseResponse.success(noteService.getByTitle(title));
    }
}
