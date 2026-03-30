package com.upchr.mytool.modules.cron.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.upchr.mytool.modules.cron.entity.JobExecution;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface JobExecutionMapper extends BaseMapper<JobExecution> {
}
