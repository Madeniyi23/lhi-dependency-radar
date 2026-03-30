from arcgis.gis import GIS
import pandas as pd
import getpass
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_targets(item):
    """Build target strings used to detect dependencies."""
    targets = []

    if item.id:
        targets.append(("item_id", item.id.lower(), "high", "direct"))

    if hasattr(item, "url") and item.url:
        service_url = item.url.lower().rstrip("/")
        targets.append(("service_url", service_url, "high", "direct"))

    try:
        if hasattr(item, "layers") and item.layers:
            for lyr in item.layers:
                lyr_id = getattr(lyr.properties, "id", None)
                lyr_url = getattr(lyr.properties, "url", None)
                if lyr_url:
                    label = f"layer_url_{lyr_id}" if lyr_id is not None else "layer_url"
                    targets.append((label, lyr_url.lower().rstrip("/"), "high", "direct"))
    except Exception:
        pass

    try:
        if hasattr(item, "tables") and item.tables:
            for tbl in item.tables:
                tbl_id = getattr(tbl.properties, "id", None)
                tbl_url = getattr(tbl.properties, "url", None)
                if tbl_url:
                    label = f"table_url_{tbl_id}" if tbl_id is not None else "table_url"
                    targets.append((label, tbl_url.lower().rstrip("/"), "high", "direct"))
    except Exception:
        pass

    return targets


def build_summary(detailed_df):
    """Build a one-row summary from the detailed dependency results."""
    if detailed_df.empty:
        return pd.DataFrame([
            {
                "total_matches": 0,
                "total_unique_using_items": 0,
                "web_maps": 0,
                "dashboards": 0,
                "web_experiences": 0,
                "web_mapping_apps": 0,
                "storymaps": 0,
                "other": 0,
                "high_confidence_matches": 0,
                "direct_dependencies": 0,
            }
        ])

    unique_items = detailed_df["using_item_id"].nunique()

    web_maps = (detailed_df["using_item_type"] == "Web Map").sum()
    dashboards = (detailed_df["using_item_type"] == "Dashboard").sum()
    web_experiences = (detailed_df["using_item_type"] == "Web Experience").sum()
    web_mapping_apps = (detailed_df["using_item_type"] == "Web Mapping Application").sum()
    storymaps = (detailed_df["using_item_type"] == "StoryMap").sum()

    other = len(detailed_df) - (
        web_maps + dashboards + web_experiences + web_mapping_apps + storymaps
    )

    high_confidence = (detailed_df["match_confidence"] == "high").sum()
    direct_dependencies = (detailed_df["dependency_level"] == "direct").sum()

    return pd.DataFrame([
        {
            "total_matches": len(detailed_df),
            "total_unique_using_items": unique_items,
            "web_maps": web_maps,
            "dashboards": dashboards,
            "web_experiences": web_experiences,
            "web_mapping_apps": web_mapping_apps,
            "storymaps": storymaps,
            "other": other,
            "high_confidence_matches": high_confidence,
            "direct_dependencies": direct_dependencies,
        }
    ])


def main():
    print("\n=== LHI Dependency Radar v1.2 ===\n")

    org_url = input("Org URL: ").strip()
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    item_id = input("Feature Layer Item ID: ").strip()

    print("\nConnecting...")
    gis = GIS(org_url, username, password)

    item = gis.content.get(item_id)

    if not item:
        print("Item not found")
        return

    print(f"Target: {item.title}")
    print(f"Type: {item.type}")

    targets = build_targets(item)

    print("\nTargets being checked:")
    for label, target, confidence, dep_level in targets:
        print(f" - {label}: {target}")

    results = []

    item_types = [
        "Web Map",
        "Dashboard",
        "Web Experience",
        "Web Mapping Application",
        "StoryMap",
    ]

    all_items = []
    seen_ids = set()

    print("\nFetching candidate items...")
    for item_type in item_types:
        found = gis.content.search(query=f'type:"{item_type}"', max_items=100)
        for found_item in found:
            if found_item.id not in seen_ids:
                seen_ids.add(found_item.id)
                all_items.append(found_item)

    print(f"Total items to scan: {len(all_items)}\n")

    for idx, using_item in enumerate(all_items, start=1):
        print(f"{idx}/{len(all_items)}: {using_item.title}")

        try:
            data = using_item.get_data()
        except Exception:
            continue

        if not data:
            continue

        data_str = str(data).lower()

        for label, target, confidence, dep_level in targets:
            if target and target in data_str:
                results.append(
                    {
                        "target_item_title": item.title,
                        "target_item_id": item.id,
                        "target_item_type": item.type,
                        "target_item_url": getattr(item, "url", ""),
                        "using_item_title": using_item.title,
                        "using_item_id": using_item.id,
                        "using_item_type": using_item.type,
                        "using_item_owner": using_item.owner,
                        "using_item_access": getattr(using_item, "access", ""),
                        "using_item_url": f"{org_url.rstrip('/')}/home/item.html?id={using_item.id}",
                        "match_type": label,
                        "matched_value": target,
                        "match_confidence": confidence,
                        "dependency_level": dep_level,
                    }
                )
                break

    detailed_df = pd.DataFrame(results)

    if detailed_df.empty:
        print("\nNo matches found.")
        summary_df = build_summary(detailed_df)
        summary_df.to_csv("dependency_summary_v1_2.csv", index=False)
        print("Empty summary saved as dependency_summary_v1_2.csv")
        return

    detailed_df = detailed_df.drop_duplicates(
        subset=["target_item_id", "using_item_id", "match_type"]
    ).sort_values(by=["using_item_type", "using_item_title", "match_type"])

    summary_df = build_summary(detailed_df)

    detailed_output = "dependency_report_v1_2.csv"
    summary_output = "dependency_summary_v1_2.csv"

    detailed_df.to_csv(detailed_output, index=False)
    summary_df.to_csv(summary_output, index=False)

    print(f"\nDone. Detailed report saved as {detailed_output}")
    print(f"Summary report saved as {summary_output}")
    print(f"Total matches after dedupe: {len(detailed_df)}")
    print(f"Total unique using items: {summary_df.iloc[0]['total_unique_using_items']}")

    try:
        from IPython.display import display

        display(detailed_df)
        display(summary_df)
    except Exception:
        pass


if __name__ == "__main__":
    main()
