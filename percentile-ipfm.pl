#!/usr/bin/perl -w
#
# ====================================================================================
#   BW-IPFM version 1.5
#   http://bw.intellos.net
#
#   by Patrick Lagace patou@sympatico.ca
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
#
# ====================================================================================
use strict;
use Time::Local;

# ====================================================================================
#    CONFIGURATION
#    You can edit those settings to customize bw
# ====================================================================================

my $CONFIGURATION_FILE="/etc/ipfm.conf"; # Location of your ipfm.conf

my $IPFM_MINUTE="00";              # Minute and Second at your log rotate,
my $IPFM_SECOND="00";              # this must be the same as your ipfm.conf.

my @data_host = ();

# Static host (OPTIONAL)
# This allow you to specify a list of host to show in every repport, by default with
# IPFM, a host who didnt used any bandwith wont appear in the repport
#  @data_host=("station1","station2","Bob","Gary","Jonh","BROADCAST");

# 95 for 95 percentile billing
my $percentile = 95;


# ====================================================================================
#    INITIALISATION
#    No need to edit anything pass this point
# ====================================================================================

sub compute_percentile($@);
sub simplification;
sub formatline;
sub sorter;
sub last_day_of_month;
sub interval;
sub help;


# Get the actual time

my @today=localtime(time);
my @month_name=("","Jannuary","February","March","April","May","June","July","August","September","October","November","December");

my $present_year  = $today[5]-100; # Because the date 1999 is 99 and 2002 is 102
my $present_month = $today[4]+1;   # Because Jan is month 0 in localtime(time)
my $present_day   = $today[3];
my $present_hour = $today[2];
my $present_minute = $today[1];

my $from_hour;
my $from_minute;
my $to_year;
my $to_month;
my $to_day;
my $to_hour;
my $to_minute;

# Set default value
my $field="total";
my $order="des";

my $ipfm_filename_id=0;
my $title="Daily Bandwith Usage for $present_day $month_name[$present_month] ".(2000+$present_year);
interval(0,0,"","","",60,24,"","","");


# Init the array
my @data_total_in = ();
my @data_total_out = ();
my @data_total_total = ();
my @data_in = ();
my @data_out = ();
my @data_total = ();
my @raw_data_in = ();
my @raw_data_out = ();
my @raw_data_total = ();

for ($a=0;$a<=$#data_host;$a++) {
  $raw_data_in[$a]=();
  $raw_data_out[$a]=();
  $raw_data_total[$a]=();
}

my @ipfm_filename=`cat $CONFIGURATION_FILE | grep -v "#" | grep FILENAME`;
for (my $n=0;$n<=$#ipfm_filename;$n++) {
  $ipfm_filename[$n]=~ s/^FILENAME\s(\S.)/$1/;
  $ipfm_filename[$n]=~ s/"//g;
}

my @ipfm_dump=`cat $CONFIGURATION_FILE | grep -v "#" | grep "DUMP EVERY"`;
my @ipfm_hour = ();
my @IPFM_MINUTE = ();
my @IPFM_SECOND = ();
for (my $n=0;$n<=$#ipfm_dump;$n++) {
  $ipfm_dump[$n]=~ s/^DUMP\sEVERY\s(\S.)/$1/;
  $ipfm_dump[$n]=~ s/"//g;
  $ipfm_hour[$n]=$ipfm_dump[$n];
  $IPFM_MINUTE[$n]=$ipfm_dump[$n];
  $IPFM_SECOND[$n]=$ipfm_dump[$n];
  if ($ipfm_hour[$n]   =~ m/(\d+)\shour/) {
    $ipfm_hour[$n] = $1;
  } else {
    $ipfm_hour[$n] = 0;
  }
  $IPFM_MINUTE[$n] =~ m/(\d+)\sminutes/;
  $IPFM_MINUTE[$n] = $1;
  
  if($IPFM_SECOND[$n] =~ m/(\d+)\sseconds/) {
    $IPFM_SECOND[$n] = $1;
  } else {
    $IPFM_SECOND[$n] = 0;
  }
}


# ====================================================================================
#    READ THE COMMAND LINE SWITCH
# ====================================================================================

my $UNIQUE_SWITCH=0;
my $argnum=0;
my $from_month;
my $from_year;
my $from_day;
my $DEBUG_MODE = 0;

while ($argnum<=$#ARGV) {

  if ($ARGV[$argnum] eq "-d") {
    $UNIQUE_SWITCH++;
    if ($argnum<$#ARGV) {
      if (($ARGV[$argnum+1] ne "-interval")&&($ARGV[$argnum+1] ne "-f")&&($ARGV[$argnum+1] ne "-o")&&($ARGV[$argnum+1] ne "-i")&&($ARGV[$argnum+1] ne "-debug")) {
        if ($ARGV[$argnum+1]=~ s/(\d+)\/(\d+)\/(\d+)/$3/) {
          interval(0,0,$1,$2,$3,60,24,$1,$2,$3);
          $present_day=$1;
          $present_month=$2;
          $present_year=$3;
          $argnum++;
        } elsif ($ARGV[$argnum+1]=~ s/(\d+)\/(\d+)/$2/) {
          interval(0,0,$1,$2,"",60,24,$1,$2,"");
          $present_day=$1;
          $present_month=$2;
          $argnum++;
        } elsif ($ARGV[$argnum+1]=~ s/(\d+)/$1/) {
          interval(0,0,$1,"","",60,24,$1,"","");
          $present_day=$1;
          $argnum++;
        } else {
          help("The value \'$ARGV[$argnum+1]\' specified for -d is invalid");
        }
      } else {
        interval(0,0,"","","",60,24,"","","");
      }
    } else {
      interval(0,0,"","","",60,24,"","","");
    }
    $title="Daily Bandwith Usage for $present_day $month_name[$present_month] ".(2000+$present_year);

  } elsif ($ARGV[$argnum] eq "-m") {
    $UNIQUE_SWITCH++;
    if ($argnum<$#ARGV) {
      if (($ARGV[$argnum+1] ne "-d")&&($ARGV[$argnum+1] ne "-from")&&($ARGV[$argnum+1] ne "-to")&&($ARGV[$argnum+1] ne "-f")&&($ARGV[$argnum+1] ne "-o")&&($ARGV[$argnum+1] ne "-i")&&($ARGV[$argnum+1] ne "-debug")) {
        if ($ARGV[$argnum+1]=~ s/(\d+)\/(\d+)/$2/) {
          interval(0,0,1,$1,$2,60,24,last_day_of_month($1,$2),$1,$2);
          $present_month=$1;
          $present_year=$2;
          $argnum++;
        } elsif ($ARGV[$argnum+1]=~ s/(\d+)/$1/) {
          interval(0,0,1,$1,"",60,24,last_day_of_month($1,$present_year),$1,"");
          $present_month=$1;
          $argnum++;
        } else {
          help("The value \'$ARGV[$argnum+1]\' specified for -m is invalid");
        }
      } else {
        interval(0,0,1,"","",60,24,last_day_of_month($present_month,$present_year),"","");
      }
    } else {
      interval(0,0,1,"","",60,24,last_day_of_month($present_month,$present_year),"","");
    }
    $title="Monthly Bandwith Usage for $month_name[$from_month] ".(2000+$from_year);

  } elsif ($ARGV[$argnum] eq "-yesterday") {
    $UNIQUE_SWITCH++;
    my $yesterday_day  =$present_day-1;
    my $yesterday_month=$present_month;
    my $yesterday_year =$present_year;
    if ($yesterday_day==0) {
      $yesterday_month--;
      if ($yesterday_month==0) {
        $yesterday_month=12;             
        $yesterday_year--;
      }
      $yesterday_day=last_day_of_month($yesterday_month,$yesterday_year);
    }
    interval(0,0,$yesterday_day,$yesterday_month,$yesterday_year,60,24,$yesterday_day,$yesterday_month,$yesterday_year);
    $title="Daily Bandwith Usage for $from_day $month_name[$from_month] ".(2000+$from_year);

  } elsif ($ARGV[$argnum] =~ s/-last(\d+)days/$1/) {
    $UNIQUE_SWITCH++;
    my $starting_day  =$present_day;
    my $starting_month=$present_month;
    my $starting_year =$present_year;
    for (my $i=0;$i<$ARGV[$argnum];$i++) {
      $starting_day--;
      if ($starting_day==0) {
        $starting_month--;
        if ($starting_month==0) {
          $starting_year--;
          $starting_month=12;
        }
        $starting_day=last_day_of_month($starting_month,$starting_year);
      }
    }
    interval(0,0,$starting_day,$starting_month,$starting_year,60,24,$present_day,$present_month,$present_year);
    $title="Bandwith Usage for the last $ARGV[$argnum] days from $from_day $month_name[$from_month] ".(2000+$from_year);

  } elsif ($ARGV[$argnum] =~ s/-last(\d+)months/$1/) {
    $UNIQUE_SWITCH++;
    my $starting_month=$present_month;
    my $starting_year =$present_year;
    for (my $i=0;$i<$ARGV[$argnum];$i++) {
      $starting_month--;
      if ($starting_month==0) {
        $starting_year--;
        $starting_month=12;
      }
    }
    interval(0,0,1,$starting_month,$starting_year,60,24,$present_day,$present_month,$present_year);
    $title="Bandwith Usage for the last $ARGV[$argnum] months from $from_day $month_name[$from_month] ".(2000+$from_year);

  } elsif ($ARGV[$argnum] eq "-interval") {
    $UNIQUE_SWITCH++;
    $ARGV[$argnum+1] =~ s/(\d+)\/(\d+)\/(\d+)-(\d+)\/(\d+)\/(\d+)/$3/;
    interval(0,0,$1,$2,$3,60,24,$4,$5,$6);
    $title="Bandwith Usage from $1 $month_name[$2] ".(2000+$3)." to $4 $month_name[$5] ".(2000+$6);
    $argnum++;
   } elsif ($ARGV[$argnum] eq "-f"){
      $field=lc $ARGV[$argnum+1];
      $argnum++;

  } elsif ($ARGV[$argnum] eq "-i") {
    $ipfm_filename_id=$ARGV[$argnum+1];
    $argnum++;

   } elsif ($ARGV[$argnum] eq "-o"){        
      $order=lc $ARGV[$argnum+1];
      $argnum++;
      
  } elsif ($ARGV[$argnum] eq "-debug") {
    $DEBUG_MODE="1";

  } elsif ($ARGV[$argnum] eq "-h") {
    help("");

  } else {
    help("\'$ARGV[$argnum]\' is not a valid argument for bw-ipfm");
  }
  $argnum++;
}
if ($UNIQUE_SWITCH>1) {
  help("-m, -d, -yesterday and -interval cannot be use for the same repport");
}

if($IPFM_MINUTE[$ipfm_filename_id] < 1
   || $IPFM_SECOND[$ipfm_filename_id] > 0
  || $ipfm_hour[$ipfm_filename_id] > 0) {
  print STDERR "Error, dumps must be every X minutes\n";
  print "#$IPFM_MINUTE[$ipfm_filename_id]#\n";
  print "#$IPFM_SECOND[$ipfm_filename_id]#\n";
  print "#$ipfm_hour[$ipfm_filename_id]#\n";
  exit;
}


# ====================================================================================
#    LOOP TO EVERY LOG BETWEEN FROM_XXXXX TO TO_XXXXX
# ====================================================================================

my $scan_year =$from_year;
my $scan_month=$from_month;
my $scan_day  =$from_day;
my $scan_hour =$from_hour;
my $scan_minute = $from_minute;

if ($DEBUG_MODE) {
  print "\nscaning $from_year $from_month $from_day $from_hour:$from_minute - $to_year $to_month $to_day $to_hour:$to_minute";
}

for ($scan_year=$from_year;$scan_year<=$to_year;$scan_year++) {

  if ($DEBUG_MODE) {
    print "\nYEAR: $scan_minute:$scan_hour:$scan_day/$scan_month/$scan_year\t$from_minute:$from_hour:$from_day/$from_month/$from_year\t$to_minute:$to_hour:$to_day/$to_month/$to_year\n";
  }
  if (($scan_year<=$to_year)&&($scan_year > $from_year)) {
    $scan_month=1;
  }


  while (( ($scan_month <= $to_month)
           && ($scan_year eq $to_year) )
         ||( ($scan_month<12)
             &&($scan_year <= $to_year) )) {

    if ($DEBUG_MODE) {
      print "\nMONTH: $scan_minute:$scan_hour:$scan_day/$scan_month/$scan_year\t$from_minute:$from_hour:$from_day/$from_month/$from_year\t$to_minute:$to_hour:$to_day/$to_month/$to_year\n";
    }
    if (($scan_month<$to_month)&&($scan_year eq $to_year)) {
      $scan_day=1;
    }


    while (( ($scan_day<=$to_day)
             &&($scan_month eq $to_month)
             &&($scan_year eq $to_year) )
           ||( ($scan_day<32)
               && (($scan_month <= $to_month)
                   ||($scan_year <= $to_year) ))) {

      if ($DEBUG_MODE) {
        print "\nDAY: $scan_minute:$scan_hour:$scan_day/$scan_month/$scan_year\t$from_minute:$from_hour:$from_day/$from_month/$from_year\t$to_minute:$to_hour:$to_day/$to_month/$to_year\n";
      }
      $scan_hour=0;


      while (( ($scan_hour<$to_hour)
               &&($scan_day eq $to_day)
               &&($scan_month eq $to_month)
               &&($scan_year eq $to_year))
             ||(($scan_hour<24)
                && (($scan_day <= $to_day)
                    ||($scan_month <= $to_month)
                    ||($scan_year <= $to_year)))) {
        
        if ($DEBUG_MODE) {
          print "\nHOUR: $scan_minute:$scan_hour:$scan_day/$scan_month/$scan_year\t$from_minute:$from_hour:$from_day/$from_month/$from_year\t$to_minute:$to_hour:$to_day/$to_month/$to_year\n";
        }
        $scan_minute = 0;
        
        while (( ($scan_minute<$to_minute)
                 &&($scan_hour eq $to_hour)
                 &&($scan_day eq $to_day)
                 &&($scan_month eq $to_month)
                 &&($scan_year eq $to_year))
               ||(($scan_minute<60)
                  &&($scan_hour <= $to_hour)
                  && (($scan_day <= $to_day)
                      ||($scan_month <= $to_month)
                      ||($scan_year <= $to_year)))) {

          if ($DEBUG_MODE) {
            print "\nMINUTE: $scan_minute:$scan_hour:$scan_day/$scan_month/$scan_year\t$from_minute:$from_hour:$from_day/$from_month/$from_year\t$to_minute:$to_hour:$to_day/$to_month/$to_year\n";
          }
          my ($scan_year_txt, $scan_month_txt, $scan_day_txt, $scan_hour_txt, $scan_minute_txt);
          
          if ($scan_year <10) {
            $scan_year_txt ="0".$scan_year;
          } else {
            $scan_year_txt =$scan_year;
          }
          if ($scan_month<10) {
            $scan_month_txt="0".$scan_month;
          } else {
            $scan_month_txt=$scan_month;
          }
          if ($scan_day  <10) {
            $scan_day_txt  ="0".$scan_day;
          } else {
            $scan_day_txt  =$scan_day;
          }
          if ($scan_hour <10) {
            $scan_hour_txt ="0".$scan_hour;
          } else {
            $scan_hour_txt =$scan_hour;
          }
          if ($scan_minute <10) {
            $scan_minute_txt ="0".$scan_minute;
          } else {
            $scan_minute_txt =$scan_minute;
          }
           
          my $log_file=$ipfm_filename[$ipfm_filename_id];
          if ($log_file=~ /%y/) {
            $log_file=~ s/\%y/$scan_year_txt/;
          }
          if ($log_file=~ /%m/) {
            $log_file=~ s/\%m/$scan_month_txt/;
          }
          if ($log_file=~ /%d/) {
            $log_file=~ s/\%d/$scan_day_txt/;
          }
          if ($log_file=~ /%H/) {
            $log_file=~ s/\%H/$scan_hour_txt/;
          }
          if ($log_file=~ /%M/) {
            $log_file=~ s/\%M/$scan_minute_txt/;
          }
          if ($log_file=~ /%S/) {
            $log_file=~ s/\%S/$IPFM_SECOND/;
          }
          chomp $log_file;

          #if ($DEBUG_MODE) {
          #  print "Checking for $log_file\n";
          #}
          if (-e $log_file) {
            if ($DEBUG_MODE) {
              print "Opening for $log_file\n";
            }
            
            open(BUFF,"$log_file") || print "Error opening $log_file: $!";
            my @current_record_file = <BUFF>;
            close (BUFF);

            foreach (@current_record_file) {
              $_ =~ s/^\n.*/#/; # if the line start by newline, comment it
              chomp $_;
              $_ =~ s/#.*/null/; # Remove comments
            }

            my $total_in = 0;
            my $total_out = 0;
            my $total_total = 0;
            foreach (@current_record_file) {
              if ($_ ne "null") {
                my $current_host = $_;
                $current_host =~ s/(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s*/$1/;
                my $current_in        = $2;
                my $current_out       = $3;
                my $current_total     = $4;
                my $finded=-1;
                for (my $a=0;$a<=$#data_host;$a++) {
                  if ($data_host[$a] eq $current_host) {
                    $finded=$a;
                  }
                }

                my $index;
                if ($finded eq -1) {
                  $index=$#data_host+1;
                } else {
                  $index = $finded;
                }
                
                $data_host[$index] = $current_host;
                push @{$raw_data_in[$index]}, $current_in;
                push @{$raw_data_out[$index]}, $current_out;
                push @{$raw_data_total[$index]}, $current_total;

                $total_in = $total_in + $current_in;
                $total_out = $total_out + $current_out;
                $total_total = $total_total + $current_total;
                     
              }
            }
            push @data_total_in, $total_in;
            push @data_total_out, $total_out;
            push @data_total_total, $total_total;
          }
          $scan_minute++;
          if ($scan_minute>60) {
            $scan_minute=0;
            $scan_hour++;
          }
        }                       # minute
        $scan_hour++;
        if ($scan_hour>24) {
          $scan_hour=0;
          $scan_day++;
        }
      }                         # hour
      $scan_day++;
      if ($scan_day>last_day_of_month($scan_month,$scan_year)+1) {
        $scan_day=1;
        $scan_month++;
      }
    }                           # day
    $scan_month++;
    if ($scan_month>13) {
      $scan_month=1;
      $scan_year++;
    }
  }                             #month
}                               #year


# compute percentiles and put the data in $data_in, $data_out, $data_total
for (my $position=0;$position<=$#data_host;$position++) {
  $data_in[$position] = compute_percentile($percentile, $raw_data_in[$position]);
  $data_out[$position] = compute_percentile($percentile, $raw_data_out[$position]);
  $data_total[$position] = compute_percentile($percentile, $raw_data_total[$position]);
}


sorter($field, $order);



# ====================================================================================
#    PRINT REPPORT
# ====================================================================================

print "$title\n";
print formatline("Hosts","In","Out","Total")."\n";
print "--------------------------------------------------------------------\n";
for (my $position=0;$position<=$#data_host;$position++) {
  my $host  =$data_host[$position];

  my $in    =simplification($data_in[$position]);
  my $out   =simplification($data_out[$position]);
  my $total =simplification($data_total[$position]);
  
  print formatline($host,$in,$out,$total)."\n";

}

print "--------------------------------------------------------------------\n";
my $totin    = simplification(compute_percentile($percentile, \@data_total_in));
my $totout   = simplification(compute_percentile($percentile, \@data_total_out));
my $tottotal = simplification(compute_percentile($percentile, \@data_total_total));
print formatline("Total:",$totin,$totout,$tottotal)."\n";

sub compute_percentile($@) {
  my ($local_percentile, $data_ref) = @_;
  my @data = @{$data_ref};
  my @sorted_data = sort sort_predicate @data;

  my $index = int($#sorted_data * $local_percentile / 100.0);

  my $multiplier = 1/ ($IPFM_MINUTE[$ipfm_filename_id] * 60);
  return $sorted_data[$index] * $multiplier;
}

sub sort_predicate {
  $b <=> $a;
}


# ====================================================================================
#    SORTER: Sort the data
#            sorter()
# ====================================================================================

sub sorter{
  my($field) = $_[0];
  my($order) = $_[1];

  for (my $i=-1; $i<$#data_host-1; $i++) {
    for (my $j=0; $j<$#data_host-($i+1); $j++) {

      my $first;
      my $second;
      if ($field eq "host") {
        $first =ord($data_host[$j+1]);
        $second=ord($data_host[$j]);
      } elsif ($field eq "in") {
        $first =$data_in[$j+1];
        $second=$data_in[$j];
      } elsif ($field eq "out") {
        $first =$data_out[$j+1];
        $second=$data_out[$j];
      } elsif ($field eq "total") {
        $first =$data_total[$j+1];
        $second=$data_total[$j];
      }
      if (($order eq "des" && $first > $second) || ($order eq "asc" && $first < $second)) {
        my $tmp = $data_in[$j];
        $data_in[$j] = $data_in[$j+1];
        $data_in[$j+1] = $tmp;
        $tmp = $data_out[$j];
        $data_out[$j] = $data_out[$j+1];
        $data_out[$j+1] = $tmp;
        $tmp = $data_host[$j];
        $data_host[$j] = $data_host[$j+1];
        $data_host[$j+1] = $tmp;
        $tmp = $data_total[$j];
        $data_total[$j] = $data_total[$j+1];
        $data_total[$j+1] = $tmp;
      }
    }
  }
}



# ====================================================================================
#    FORMATLINE: Format 1 line of result for printing
#                formatline($host,$in,$out,$total)
# ====================================================================================

sub formatline{
  my($host) = $_[0];
  my($in)   = $_[1];
  my($out)  = $_[2];
  my($total)= $_[3];
  my $spacehost="";

  # compute host column width to be max hostname + 2
  my $host_column_width = 25;
  for ($a=0;$a<=$#data_host;$a++) {
    my $len = length $data_host[$a];
    if($len > $host_column_width) {
      $host_column_width = $len;
    }
  }
  $host_column_width = $host_column_width + 2;
  
  for (my $nbspace=1;$nbspace<$host_column_width-(length $host);$nbspace=$nbspace+1) {
    $spacehost=$spacehost." ";
  }
  my $spacein="";
  for (my $nbspace=1;$nbspace<10-(length $in);$nbspace=$nbspace+1) {
    $spacein=$spacein." ";
  }
  my $spaceout="";
  for (my $nbspace=1;$nbspace<10-(length $out);$nbspace=$nbspace+1) {
    $spaceout=$spaceout." ";
  }
  my $result="$host $spacehost $in $spacein $out$ spaceout $total";
  return $result;
}



# ====================================================================================
#    SIMPLIFICATION: Change the scale of size for easier reading
#                    simplification($size)
# ====================================================================================

sub simplification{
  my($sizep)=@_;
  if ($sizep > 1000000000) {
    $sizep = $sizep/1000000000;
    $sizep = sprintf("%.2f",$sizep);
    $sizep = $sizep."Gps";
  } elsif ($sizep > 1000000) {
    $sizep = $sizep/1000000;
    $sizep = sprintf("%.2f",$sizep);
    $sizep = $sizep."Mps";
  } elsif ($sizep > 1000) {
    $sizep = $sizep/1000;
    $sizep = sprintf("%.2f",$sizep);
    $sizep = $sizep."Kps";
  } else {
    $sizep = sprintf("%.2f",$sizep);
    $sizep = $sizep."Bps";
  }
  return $sizep;
}


# ====================================================================================
#    INTERVAL: Allo to assign easily the from and to limits
#              interval($from_minute,$from_hour,$from_day,$from_month,$from_year,$to_minute,$to_hour,$to_day,$to_month,$to_year)
# ====================================================================================



sub interval{
  if ($_[0] eq "") {
    $from_minute   = $present_minute;
  } else {
    $from_minute   = int $_[0];
  }
  if ($_[1] eq "") {
    $from_hour   = $present_hour;
  } else {
    $from_hour   = int $_[1];
  }
  if ($_[2] eq "") {
    $from_day    = $present_day;
  } else {
    $from_day    = int $_[2];
  }
  if ($_[3] eq "") {
    $from_month  = $present_month;
  } else {
    $from_month  = int $_[3];
  }
  if ($_[4] eq "") {
    $from_year   = $present_year;
  } else {
    $from_year   = int $_[4];
  }
  if ($_[5] eq "") {
    $to_minute     = $present_minute;
  } else {
    $to_minute = int $_[5];
  }
  if ($_[6] eq "") {
    $to_hour     = $present_hour;
  } else {
    $to_hour     = int $_[6];
  }
  if ($_[7] eq "") {
    $to_day      = $present_day;
  } else {
    $to_day      = int $_[7];
  }
  if ($_[8] eq "") {
    $to_month    = $present_month;
  } else {
    $to_month    = int $_[8];
  }
  if ($_[9] eq "") {
    $to_year     = $present_year;
  } else {
    $to_year     = int $_[9];
  }
}


# ======================================================
#    LAST_DAY_OF_MONTH: Return the last day of month of year specify in argument
#                       last_day_of_month($month,$year)
# ======================================================

sub last_day_of_month{
  my($month) = $_[0];
  my($year) = $_[1]+2000;
  my $time = timegm(35,12,20,12,4,2001);
  my $year2;
  my $month2;
  if ($month == 12) {
    $year2 = $year + 1;
    $month2 = 1;
  } else {
    $month2 = $month+1;
    $year2 = $year;
  }
  $time = timegm(0,0,0,1,$month2-1,$year2);
  my $lastday = scalar gmtime($time-24*3600);
  $lastday =~ s/\w+\s\w+\s(\d+)\s\d+:\d+:\d+\s\d+/$1/;
  return $lastday;
}



# ======================================================
#    HELP: Display usage and quit with error
#          help($message)
# ======================================================


sub help{
  my($errormessage)=@_;
  print "$errormessage\n\n";
  print "USAGE: ./bw [-d [DD][/MM][/YY] | -m [MM][/YY] | [-interval DD/MM/YY-DD/MM/YY]][-f (host|in|out|total)][-o (asc|des)][-i ID][-h]\n";
  print "If no argument are specify, -d is assume\n";
  print "-d [DD][/MM][/YY]      generate a daily repport\n";
  print "                       (current day of current month of current year is used if none are specify\n";
  print "-m [MM][/YY]           generate a monthly repport\n";
  print "                       (curent month of current year is used if none are specify)\n";
  print "-yesterday             generate a daily repport for yesterday\n";
  print "-lastXXdays             generate a repport for the last XX days\n";
  print "-lastXXmonths          generate a repport for the last XX months\n";
  print "-interval DD/MM/YY-DD/MM/YY    specify the interval for the repport\n";
  print "-i ID                   Specify wich FILENAME you want to use from your ipfm.conf\n";
  print "                       (usefull only if you have multipe FILENAME instance in your ipfm.conf)\n";
  print "-f [host|in|out|total] specify the field to sort on, can be host, in, out or total\n";
  print "-o [asc|des]           specify the order to sort on, can be asc ascending or des for descending\n";  print "-debug                 Print repport and debugging information\n";
  print "-h                     Print this help\n";
  exit 1;
}


exit 0;
__END__
