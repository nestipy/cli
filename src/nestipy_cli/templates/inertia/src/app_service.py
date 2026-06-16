from nestipy.common import Injectable


@Injectable()
class AppService:
    def greeting(self) -> str:
        return "Welcome to Nestipy + Inertia.js"

    def stats(self) -> dict:
        return {"users": 42, "online": 7}
