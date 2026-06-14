import re
import xml.etree.cElementTree as ET

G_ORDER_TYPE_KEY = 1
G_INTERSECT_TYPE_KEY = 2


class SubtitleItem(object):
    begin: int
    end: int
    subtitle: str

    def __str__(self):
        return f"begin: {self.begin}, end: {self.end}, subtitle: {self.subtitle}"

    pass


class SubtitleBean(object):
    subtitle_list: list

    def __init__(self):
        self.subtitle_list = []

    def add_item(self, item: SubtitleItem):
        self.subtitle_list.append(item)

    def get_item_list(self) -> list:
        return self.subtitle_list

    def get_item_count(self) -> int:
        return len(self.subtitle_list)

    def get_first_item(self) -> SubtitleItem or None:
        if len(self.subtitle_list) == 0:
            return None
        return self.subtitle_list[0]

    def print(self):
        for item in self.subtitle_list:
            print(f"{item}")

    pass


def convert_subtitle_str_to_timestamp(ts: str) -> int:
    if ts is None or ts.isspace():
        return 0
    ts_split = ts.split(',')
    if len(ts_split) != 2:
        return 0
    micro_sec = int(ts_split[1])
    ts2_split = ts_split[0].split(':')
    if len(ts2_split) != 3:
        return 0
    hour = int(ts2_split[0])
    minute = int(ts2_split[1])
    second = int(ts2_split[2])
    return hour * 3600000 + minute * 60000 + second * 1000 + micro_sec


def convert_subtitle_timestamp_to_str(ts_msec: int) -> str or None:
    if ts_msec < 0:
        return None
    hour = ts_msec // 3600000
    ts_msec = ts_msec - (hour * 3600000)
    minute = ts_msec // 60000
    ts_msec = ts_msec - (minute * 60000)
    second = ts_msec // 1000
    ts_msec = ts_msec - (second * 1000)
    msec = ts_msec
    return f"{hour:02d}:{minute:02d}:{second:02d},{msec:03d}"


def convert_subtitle_to_bean(intput_file: str, is_english: bool) -> SubtitleBean:
    bean = SubtitleBean()
    ttml = "http://www.w3.org/ns/ttml"
    tree = ET.parse(intput_file)
    root = tree.getroot()
    if root.tag != f"{{{ttml}}}tt":
        return bean
    body = root.find(f"{{{ttml}}}body")
    for element in body.iter(f"{{{ttml}}}p"):
        ele_cont = (' '.join(element.itertext()))
        if is_english:
            ele_cont = re.sub(r'[^\x00-\x7f]', r' ', ele_cont)
            ele_cont = ele_cont.lower().replace('[music]', '')
            ele_cont = ele_cont.lower().replace('music]', '')
        begin = convert_subtitle_str_to_timestamp(element.attrib.get("begin").replace('.', ',').strip())
        end = convert_subtitle_str_to_timestamp(element.attrib.get("end").replace('.', ',').strip())
        item = SubtitleItem()
        item.subtitle = ele_cont.strip()
        item.begin = begin
        item.end = end
        bean.add_item(item)
    return bean


def convert_subtitle_intersect(bean: SubtitleBean, output_file: str) -> bool:
    if not bean or not bean.get_first_item():
        return False
    last_begin = bean.get_first_item().begin
    last_end = bean.get_first_item().end
    subtitle = ''
    seq_num = 1
    count = 0
    with open(output_file, 'w+') as fp:
        for item in bean.get_item_list():
            count = count + 1
            if item.begin < last_end:
                if subtitle.strip() == "":
                    subtitle = f"{item.subtitle}"
                else:
                    subtitle = f"{subtitle} {item.subtitle}"
                if count == bean.get_item_count():
                    if subtitle.strip() != '':
                        fp.write(f"{seq_num}\n")
                        fp.write(
                            f"{convert_subtitle_timestamp_to_str(last_begin)} --> {convert_subtitle_timestamp_to_str(last_end)}\n")
                        fp.write(f"{subtitle}\n\n")
                continue
            if subtitle.strip() != '':
                fp.write(f"{seq_num}\n")
                fp.write(
                    f"{convert_subtitle_timestamp_to_str(last_begin)} --> {convert_subtitle_timestamp_to_str(last_end)}\n")
                fp.write(f"{subtitle}\n\n")
                seq_num = seq_num + 1
            subtitle = item.subtitle
            last_begin = item.begin
            last_end = item.end
            if count == bean.get_item_count():
                if subtitle.strip() != '':
                    fp.write(f"{seq_num}\n")
                    fp.write(
                        f"{convert_subtitle_timestamp_to_str(last_begin)} --> {convert_subtitle_timestamp_to_str(last_end)}\n")
                    fp.write(f"{subtitle}\n\n")
        # 因为是后置方式处理subtitle的，所以，需要最后判断一下，count是否与item count是否一致
    pass


def convert_subtitle_order(bean: SubtitleBean, output_file: str):
    if not bean:
        return False
    count = 1
    with open(output_file, 'w+') as fp:
        for item in bean.get_item_list():
            if item.subtitle.strip() != '':
                fp.write(f"{count}\n")
                fp.write(
                    f"{convert_subtitle_timestamp_to_str(item.begin)} --> {convert_subtitle_timestamp_to_str(item.end)}\n")
                fp.write(f"{item.subtitle}\n\n")
                count = count + 1
    return True


def check_subtitle_time_order(bean: SubtitleBean):
    global G_ORDER_TYPE_KEY, G_INTERSECT_TYPE_KEY
    last_end_msec = 0
    for item in bean.get_item_list():
        if (item.begin < last_end_msec):
            return G_INTERSECT_TYPE_KEY
        last_end_msec = item.end
    return G_ORDER_TYPE_KEY


def convert_subtitle_ttml_to_srt(input_file: str, output_file: str, is_english: bool) -> bool:
    global G_ORDER_TYPE_KEY, G_INTERSECT_TYPE_KEY
    bean = convert_subtitle_to_bean(input_file, is_english)
    if not bean or len(bean.get_item_list()) == 0:
        return False
    order_type = check_subtitle_time_order(bean)
    if order_type == G_ORDER_TYPE_KEY:
        convert_subtitle_order(bean, output_file)
    elif order_type == G_INTERSECT_TYPE_KEY:
        convert_subtitle_intersect(bean, output_file)
    return True


if __name__ == "__main__":
    input = 'st_a069daec8995cfc3557889b57ef4bca7.en.ttml'
    output = 'st_a069daec8995cfc3557889b57ef4bca7.en.srt'
    convert_subtitle_ttml_to_srt(input, output, True)
