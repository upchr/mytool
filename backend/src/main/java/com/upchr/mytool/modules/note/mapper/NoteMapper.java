package com.upchr.mytool.modules.note.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.upchr.mytool.modules.note.entity.Note;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface NoteMapper extends BaseMapper<Note> {
}
