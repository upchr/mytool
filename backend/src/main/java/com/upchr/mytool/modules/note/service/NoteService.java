package com.upchr.mytool.modules.note.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.upchr.mytool.modules.note.entity.Note;
import com.upchr.mytool.modules.note.mapper.NoteMapper;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 便签服务
 */
@Service
public class NoteService extends ServiceImpl<NoteMapper, Note> {

    public List<Note> getAllNotes() {
        return list();
    }

    public Note createNote(Note note) {
        save(note);
        return note;
    }

    public Note updateNote(Long id, Note note) {
        note.setId(id);
        updateById(note);
        return note;
    }

    public boolean deleteNote(Long id) {
        return removeById(id);
    }

    public void batchDelete(List<Long> ids) {
        removeByIds(ids);
    }

    public Note getByTitle(String title) {
        return lambdaQuery().eq(Note::getTitle, title).one();
    }
}
