from worlds.LauncherComponents import Component, Type, components, launch, icon_paths

def run_client(*args: str) -> None:
    from .client.Launch import launch_GoalSaw_client

    launch(launch_GoalSaw_client, name="GoalSaw Client", args=args)

icon_paths["portalpelago"] = f"ap:{__name__}/data/Portalpelago.png"

components.append(
    Component(
        "GoalSaw Client",
        func=run_client,
        game_name="Goalsaw",
        component_type=Type.CLIENT,
        supports_uri=True,
        icon='portalpelago'
    )
)