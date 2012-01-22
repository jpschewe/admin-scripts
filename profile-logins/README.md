This is a little script to track ssh and mail logins and the number of
sites that these logins are done from. If the number of logins or the
number of sites is outside of 2 standardard deviations from the norm,
then an error is signaled.

TODO
====
* Add purge option to remove data for a user over an interval when
  something happens will skew the average and shouldn't be considered
* Add option to display all profile data for a user
