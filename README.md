# Campus RideShare Matcher MVP (Notre Dame)

High Level Project Overview: Application that matches students into shared Uber groups when leaving campus for breaks based on trip times, destination, and pickup location

This project is a Python command-line MVP that matches Notre Dame students into shared Uber groups when they are leaving campus for breaks or trips. The app reads ride requests from a CSV file, validates campus meetup locations against a separate editable list, checks compatibility, and prints matched groups plus unmatched students. It is an offline matcher only and does not attempt to book rides.

The matching logic uses four rules. Two students are compatible only if they have the same trip date, the same destination, share at least one meetup location, and have a time overlap of at least 15 minutes between earliest and latest departure times. A greedy grouping strategy then builds sensible groups while enforcing the Uber rider limit of 6 people per group. For each group, the output includes destination, rider names, shared meeting location, meeting time, and a randomly selected rider who calls the Uber.

Allowed destinations are currently restricted to `ORD`, `MDW`, and `SBN`. Meetup locations are loaded from `campus_locations.txt` and can be edited there without changing code.

The pairwise compatibility phase compares many request pairs, so runtime grows roughly as `O(n^2)`. Timing analysis was measured using synthetic datasets and averages over 5 trials:
- Small dataset (`n=20`): total ~`0.000100s`
- Large dataset (`n=500`): total ~`0.036723s`

## Files

- `README.md`
- `Makefile`
- `parser.py`
- `matching.py`
- `timing.py`
- `tests/`
- `campus_locations.txt`
- `data/demo_requests.csv`

## CSV Input Schema

`name,destination,willing_areas,date,earliest,latest`

Example row:

`Alice,ORD,"Library Circle;Main Circle",2026-05-10,14:00,15:30`

## Commands

- `make test` - run unit tests
- `make demo` - run matcher on sample demo CSV
- `make timing` - run timing analysis for small and large datasets

## Relevant Data Structure Concept:
1. Graph: Probably the most important, and was used to store "connection requests" from riders as nodes and compatibility as undirected edges. This enables the greedy algorithm to quickly find all groups based on compatability. Used an adjacency list, but instead of being a dicitonary of lists I made it a dictionary of sets since it should be a simple graph with no more than one edge between two nodes.
2. Set: Used a lot for matching compatability. Used internally in the graph as explained above but also for things like willing_areas to quickly evaluate whether two people were willing to meet at a particular location.

## Project Workflow:
1. Inputs: data/demo_requests.csv and campus_locations.txt
2. parser.py
    - Reads CSV rows
    - Validates destination, date, time, and location fields
    - Returns requests along with any errors
3. matching.py
    - Builds compatibility graph
    - Greedy algorithm to form groups of up to size 6
    - Computes meeting location/time with designated Uber caller
    - Prints matched groups and unmatched students
    - Builds unmatched list and starts again

## Performance

- Time Complexity: O(n^2 log(n))
    - Parsing/validation: (O(n))
    - Building Compatability Graph: (O(n^2)) pair checks
    - Reconfiguring Top Compatible Matches: (O(n^2 * log(n)))
        - This is from constantly sorting through a while loop to find the most compatible matches

- Space Complexity: O(n^2)
    - Requests list: (O(n))
    - Compatibility graph (adjacency list): (O(n^2))
    - Other helper structures: (O(n))

## Challenges
1. Deciding the scope of the project was a little tough for me. I wanted originally to do something with Djiketra and allowing users to simply input an address but that would add a lot of components to the project and is way more complex to implement. I also wanted to do pricing calculatons between Uber and Lyft to determine which platform a user should choose as well as what kind of vehicle given the amount of luggage they were bringing and how many people they were comfortable sharing a ride with. On the other hand I obviously didn't want to make it too simple so I added a lot of different factors into matching such as date, time, destination, and meeting location.
2. Trouble with algorithm to pair people up. At first I wasn't sure about what algorithm to use to put people into groups once they were all in a graph. Constantly popping and readjusting the graph would be pretty difficult so I think a better option would just be using a greedy algorithm to find to put people in a list for those who are unmatched and essentially keep trying to fit them into groups until you can't anymore.

## Improvements
1. I think that one area of improvement was the algorithm I used to match people. Right now, it's just a greedy algorithm that matches any people who are in a group and essentially tries to cram as many people as possible into a group. However, I think there's opportunity to optimize the algorithm so that you don't cram people together and you evaluate compatability as a sliding scale rather than just a binary yes or no.
2. There's no convinient input mechanism right now, so I think that creating a frontend UI where a user can send in requests would be nice. I also think that in a real practical scenario this would be able to be accessed in real time and users on separate devices can send requests in and get matched.

## Learning
1. I think a good high level skill that I built was being able to conceptually piece together an entire codebase. Usually in class and homework assignments we only focus on one independent program at a time, but here it was important to piece together not just multiple functions but multiple files together to build a feature.
2. I think I learned a lot about parsing in python; usually we do a lot of this in C for the classes I've taken so seeing how it's done in python with different functions is very useful. I think understanding the which data type and the formatting I want my information to be in matters a lot which was necessary to turn the csv file into data that I could modify and use in the algorithm.
3. I also learned a lot more about testing. Having to make my own tests is a lot is a lot different from what I'm used to since in class usually the tests are already written for you. Learning how each unit test is supposed to test a specific feature was important and also how to consider edge cases was very useful.

## Real-World Relevance
I think that this project could actually be useful for students on campus who want to coordinate ride sharing on campus. I've heard a lot from my friends who go back home during break and oftentimes it's very messy to coordinate times and locations with others. Obviously right now this is just the algorithm and it's still pretty rudimentary but the core logic is there.

## Use of AI Tools
- I followed Professor Brockman's advice spend a lot of time just planning with an agent and I think it was extremely helpful. It helped me clarify the scope of the project, the process flow (the files and functions I would need), and the approaches I should take for constructing the project (such as the greedy algorithm).
- It was also great for debugging, and also introduced a lot of new functions and tools that made my code much more readable and efficient.
- It also helped a lot with unit testing. Given how I had pretty much no experience writing tests, it walked me through the entire process end to end and was great for figuring out which tests to consider and how they should be implemented.