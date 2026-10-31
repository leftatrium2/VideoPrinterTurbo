from utils import const


class LipSyncBean:
    lip_sync_type: int = const.TASK_CONFIG_LIP_SYNC_NONE
    sync_labs_apikey: str = ""
    fal_latent_sync_apikey: str = ""
    hey_gen_apikey: str = ""
    remote_base_url: str = ""
    remote_api_key: str = ""
    lip_sync_full_path: str = ""

    def __str__(self) -> str:
        return "LipSyncBean{" \
            + "lip_sync_type=" + str(self.lip_sync_type) \
            + ", sync_labs_apikey='" + self.sync_labs_apikey + '\'' \
            + ", fal_latent_sync_apikey='" + self.fal_latent_sync_apikey + '\'' \
            + ", hey_gen_apikey='" + self.hey_gen_apikey + '\'' \
            + ", remote_base_url='" + self.remote_base_url + '\'' \
            + ", remote_api_key='" + self.remote_api_key + '\'' \
            + ", lip_sync_full_path='" + self.lip_sync_full_path + '\'' \
            + "}"
