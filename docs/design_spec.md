# Car Buyer Tracker
The car buyer app is designed to aggregate listings for cars similar to a Carvana or a Carfax application, except sorted by features that the user actually cares about, with an interactive map view showing where the dealerships are, and tracking how long the car has been on the lot.

This is primarily designed to replace having multiple tabs open or having a spreadsheet with information that has to be manually checked.

# Key features
## Car addition
Car addition should support the following fields:
- Website
- Dealership location
- Listed sale price (this should have a historical tracking view too to know when it's "time to move" on a car if the dealer has lowered a price, etc)
- Date first seen
- Car year
- make
- model
- trim level
- List of key features the user cares about (explained more below)
- A photo of the car parsed from the picture of a url either automatically or given by the user if an obvious one is not available.

Ideally, these fields could be parsed from just a url. The key features the car has should be scrutinized more and available to modify by the user (dealership websites are not very reliable for information)

### Key features user cares about
This should be an expandable list that the user can select that a car does or doesn't have
Initial features:
- Drivetrain type (gas, hybrid, phev, ev)
- Drive type: FWD, RWD, AWD, 4x4
Safety features are also in this, but probably tracked via a seperate category with the initial values below
- Parking sensors (boolean)
- 360 camera view (boolean)
- Seat material type (cloth, cloth/leather, leather)
- Heated seats
- Ventilated seats

# Car refreshing
- Every non-deterministic time during normal waking hours at non-fixed times the system should try to refresh to verify all tracked cars are available. If the page seems to show that the car has been removed, the system should set a flag on the car record to get the user to veriyf the car has been sold from the lot.
- e.g. run this at 8am +- 2 hrs, and also again at 6 pm +- 2 hrs. These shoudl be configurable by the user.
An additional "refresh now" should also be part of the system in cases of wanting to be able to get the most up to date information right now.

# Map view
The map view should display an overlay of a map with all the cars placed on them. Tapping on it should bring up a brief view that shows the following information:
- Picture
- year, make, model, trim
- (Time on the lot as compared to date today minus first day seen (in days, e.g. 31 days, not fractional precision))
- Current price (and if price has varied over time, the comparison of current price to all time high)

## filtering
The map should also allow the user to filter by features described above, including price

## Table view
There shoudl be another page that displays all of this information in a neat table view, allowing for typical sorting/filtering operations on any fields.
