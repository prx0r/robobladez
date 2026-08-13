from robobladez.policy import CounterPolicy

# MVP: policies are trusted in-process Python objects.
# Open-league milestone: execute policies out-of-process behind a narrow protocol
# inspired by Robocode Tank Royale.

policy = CounterPolicy(
    patience=0.85,
    punish_threshold=1.0,
)
