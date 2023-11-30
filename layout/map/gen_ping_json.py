import argparse
import csv
import json


def main():
    parser = argparse.ArgumentParser(
        description='Parse wonderproxy pings to a json file')
    parser.add_argument('servers_csv', help='Path to the servers CSV file')
    parser.add_argument('pings_csv', help='Path to the pings CSV file')

    args = parser.parse_args()

    try:
        # Load servers
        servers = []

        with open(args.servers_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                servers.append(row)

        # Load pings
        pings = []

        with open(args.pings_csv, 'r', newline='') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            pings = list(csv.reader(csv_file, delimiter=","))

        # Process
        for s in servers:
            s["pings"] = {}

        for p in pings:
            fromServer = next(
                (s for s in servers if s["id"] == str(p[0])), None)

            if not fromServer:
                continue

            if p[1] in fromServer["pings"]:
                fromServer["pings"][str(p[1])].append(float(p[4]))
            else:
                fromServer["pings"][str(p[1])] = [float(p[4])]

        for s in servers:
            for dest in s["pings"]:
                s["pings"][dest] = sum(s["pings"][dest])/len(s["pings"][dest])

        with open("pings.json", 'w') as outfile:
            json.dump(servers, outfile, sort_keys=True, indent=2)

    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
