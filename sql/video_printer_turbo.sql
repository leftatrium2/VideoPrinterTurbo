create table vpt_asr_config
(
    id                       integer                     not null
        constraint vpt_asr_config_pk
            primary key autoincrement,
    tencent_cloud_secret_id  text    default ''          not null,
    tencent_cloud_secret_key text    default ''          not null,
    xfyun_appid              text    default ''          not null,
    xfyun_secret_key         text    default ''          not null,
    xfyun_web_api            text    default ''          not null,
    local_whisper_type       integer default 3           not null,
    azure_subscription_key   text    default ''          not null,
    azure_region             text    default ''          not null,
    openai_api_key           text    default ''          not null,
    openai_model             text    default 'whisper-1' not null,
    openai_base_url          text    default ''          not null,
    volcengine_appid         text    default ''          not null,
    volcengine_access_token  text    default ''          not null,
    remote_whisper_type      integer default 1           not null,
    remote_vllm_url          text    default ''          not null,
    remote_vllm_model        text    default ''          not null,
    remote_whisper_cpp_url   text    default ''          not null
);

create table vpt_llm_config
(
    id             integer         not null
        constraint vpt_llm_config_pk
            primary key autoincrement,
    base_url       text default '' not null,
    api_key        text default '' not null,
    provider_name  text default '' not null,
    llm_model_name text default '' not null,
    memo           text default '' not null
);

create table vpt_proxy_config
(
    id                    integer            not null
        constraint vpt_proxy_config_pk
            primary key autoincrement,
    proxy_server_type     integer default 0  not null,
    proxy_server_url      text    default '' not null,
    proxy_server_username text    default '' not null,
    proxy_server_password text    default '' not null
);

create table vpt_task_logs
(
    id        integer            not null
        constraint vpt_task_logs_pk
            primary key,
    task_id   text    default '' not null,
    task_logs text    default '' not null,
    status    integer default 0  not null
);

create table vpt_tasks
(
    id                             integer                                        not null
        constraint vpt_tasks_pk
            primary key autoincrement,
    task_url                       TEXT    default ''                             not null,
    create_time                    TEXT    default (datetime('now', 'localtime')) not null,
    is_deleted                     integer default 0                              not null,
    task_status                    integer default 0                              not null,
    task_id                        text    default ''                             not null
        constraint vpt_tasks_task_id_uk
            unique,
    is_rewrite_to_tts              integer default 0                              not null,
    is_llm                         integer default 0                              not null,
    is_publish                     integer default 0                              not null,
    is_from_asr_or_subtitle        integer default 0                              not null,
    llm_prompt                     text    default ''                             not null,
    is_rewrite_to_subtitle         integer default 0                              not null,
    is_bgm                         integer default 0                              not null,
    is_video_material              integer default 0                              not null,
    tts_speed                      REAL    default 0                              not null,
    subtitle_size                  integer default 0                              not null,
    uploaded_bgm                   text    default ''                             not null,
    bgm_volume                     REAL    default 0                              not null,
    video_material_type            text    default ''                             not null,
    uploaded_video_material        text    default ''                             not null,
    video_material_splicing_mode   integer default 0                              not null,
    video_material_transition_mode integer default 0                              not null,
    video_material_video_ratio     integer default 0                              not null,
    video_material_max_duration    integer default 0                              not null,
    video_material_generate_count  integer default 0                              not null,
    subtitle_font                  text    default ''                             not null,
    subtitle_font_color            integer default 0                              not null,
    subtitle_border_color          integer default 0                              not null,
    audio_rewrite_type             integer default 0                              not null,
    tts_server                     text    default ''                             not null,
    tts_voice                      text    default ''                             not null,
    tts_volume                     REAL    default 0                              not null,
    subtitle_position              text    default ''                             not null,
    subtitle_lang                  integer default 0                              not null,
    is_use_proxy                   integer default 0                              not null,
    video_material_keyword         text    default ''                             not null,
    task_upload_video_path         text    default ''                             not null,
    task_original_video_path       text    default ''                             not null,
    task_message                   text    default ''                             not null,
    pipeline_status                integer default 0                              not null
);

create index vpt_tasks_task_status_index
    on vpt_tasks (task_status);



create table vpt_tts_config
(
    id         integer            not null
        constraint vpt_tts_config_pk
            primary key autoincrement,
    tts_server integer default 0  not null,
    tts_voice  TEXT    default '' not null,
    tts_area   text    default '' not null,
    tts_apikey text    default '' not null
);

create table vpt_tts_voice_config
(
    id                integer         not null
        constraint vpt_tts_voice_config_pk
            primary key autoincrement,
    tts_server_name   text default '' not null,
    tts_voice_content text default '' not null,
    tts_server_time   text default '' not null
);

create table vpt_video_config
(
    id                         integer           not null
        constraint vpt_video_config_pk
            primary key autoincrement,
    video_source               integer default 0 not null,
    video_joint_mode_type      integer default 0 not null,
    video_transition_mode_type integer default 0 not null,
    video_ratio_type           integer default 0 not null,
    video_fragment_duration    integer default 0 not null
);

create table vpt_video_material_pexels_config
(
    id             integer         not null
        constraint vpt_video_material_pk
            primary key autoincrement,
    pexels_api_key text default '' not null
);

create table vpt_video_material_pixabay_config
(
    id              integer         not null
        constraint vpt_video_material_pixabay_config_pk
            primary key autoincrement,
    pixabay_api_key text default '' not null
);

