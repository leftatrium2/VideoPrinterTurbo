from typing import Optional


def build_requests_proxies(proxy: Optional[str]) -> Optional[dict]:
    """
    将单个代理地址（如 "http://127.0.0.1:7890"）转换为 requests 库所需的 proxies 字典。
    http/https 请求统一走同一个代理地址；不传 proxy 则返回 None（不使用代理）。
    """
    if not proxy:
        return None
    """
    socks5:// 使用客户端 DNS 解析，socks5h:// 使用远端（代理服务器）DNS 解析。大多数场景推荐使用 socks5h://，避免本地 DNS 污染问题
    """
    if proxy.startswith("socks5://"):
        proxy = proxy.replace("socks5://", "socks5h://", 1)
    """
    requests 需要 PySocks 来支持 socks5 等socks代理
    """
    return {"http": proxy, "https": proxy}


def build_yt_dlp_proxies(proxy: Optional[str]) -> Optional[str]:
    """
    将单个代理地址（如 "http://127.0.0.1:7890"）转换为 requests 库所需的 proxies 字典。
    http/https 请求统一走同一个代理地址；不传 proxy 则返回 None（不使用代理）。
    """
    if not proxy:
        return None
    """
    socks5:// 使用客户端 DNS 解析，socks5h:// 使用远端（代理服务器）DNS 解析。大多数场景推荐使用 socks5h://，避免本地 DNS 污染问题
    """
    if proxy.startswith("socks5://"):
        proxy = proxy.replace("socks5://", "socks5h://", 1)
    return proxy
