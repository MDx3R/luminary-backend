from pydantic import BaseModel


class RabbitMQConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    vhost: str = "/"
    ssl: bool = False

    @property
    def url(self) -> str:
        scheme = "amqps" if self.ssl else "amqp"
        return f"{scheme}://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"
