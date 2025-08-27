class BaseFetcher:
    name: str = ""
    source_url: str = ""

    def fetch(self):
        raise NotImplementedError


