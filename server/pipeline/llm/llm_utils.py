import json
import re
import time


class LLMUtils:
    @staticmethod
    def build_rewrite_prompt(texts, user_instruction):
        """构造让 LLM 严格按 JSON 数组返回、且数量必须一致的 prompt"""
        numbered_input = "\n".join(
            f"{{\"id\": {i}, \"text\": {json.dumps(t, ensure_ascii=False)}}}"
            for i, t in enumerate(texts)
        )

        system_prompt = (
            "你是一个字幕改写助手。你会收到一个 JSON 数组，每个元素包含 id 和 text（字幕原文）。"
            "请根据用户指令改写每一条 text，但必须严格保持：\n"
            "1. 输出数组长度与输入完全一致，不能合并、拆分、增加或删除条目。\n"
            "2. 每个元素的 id 必须与输入一一对应，不能改变顺序。\n"
            "3. 只改写 text 字段内容，不要添加解释、注释或其他文字。\n"
            "4. 直接输出合法 JSON 数组，不要包含 ```json 代码块标记，不要有多余文字。\n"
            "5. 保留字幕原有的换行风格（如果原文有多行，可根据需要保留多行）。"
        )

        user_prompt = (
            f"改写指令：{user_instruction}\n\n"
            f"待改写的字幕数组（共 {len(texts)} 条）：\n"
            f"[{numbered_input}]"
        )
        return system_prompt, user_prompt

    @staticmethod
    def rewrite_batch(client, model, texts, user_instruction, max_retries=3):
        """调用 LLM 改写一批字幕文本，返回改写后的文本列表（严格与输入等长）"""
        system_prompt, user_prompt = LLMUtils.build_rewrite_prompt(texts, user_instruction)

        for attempt in range(max_retries):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            raw = response.choices[0].message.content.strip()

            # 兼容模型偶尔仍然加了 ```json 代码块的情况
            raw = re.sub(r"^```json\s*|\s*```$", "", raw.strip())

            try:
                result = json.loads(raw)
                if len(result) != len(texts):
                    raise ValueError(
                        f"返回数量不匹配：期望 {len(texts)} 条，实际 {len(result)} 条"
                    )
                # 按 id 排序，确保顺序正确
                result.sort(key=lambda x: x["id"])
                return [item["text"] for item in result]
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"[警告] 第 {attempt + 1} 次尝试解析失败：{e}，重试中...")
                time.sleep(1)

        raise RuntimeError(f"改写失败，已重试 {max_retries} 次仍无法获得合法结果")

    @staticmethod
    def rewrite_srt(
            client,
            model,
            subtitles,
            user_instruction,
            batch_size=50,
    ):
        """分批改写所有字幕文本，返回改写后的 subtitles（时间轴不变）"""
        new_subtitles = []
        total = len(subtitles)

        for start in range(0, total, batch_size):
            batch = subtitles[start:start + batch_size]
            texts = [s["text"] for s in batch]

            print(f"正在处理第 {start + 1} ~ {start + len(batch)} 条字幕（共 {total} 条）...")
            new_texts = LLMUtils.rewrite_batch(client, model, texts, user_instruction)

            for sub, new_text in zip(batch, new_texts):
                new_subtitles.append({
                    "index": sub["index"],
                    "start": sub["start"],  # 时间轴完全保留原值
                    "end": sub["end"],  # 时间轴完全保留原值
                    "text": new_text,
                })

        return new_subtitles
