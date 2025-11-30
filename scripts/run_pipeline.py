import json
from bankdata_pipeline import load_settings, run_pipeline


def main() -> None:
    settings = load_settings()
    artifacts = run_pipeline(settings)
    print("\nPipeline run completed. Artifacts:")
    print(json.dumps(artifacts, indent=2, default=str))


if __name__ == "__main__":
    main()
