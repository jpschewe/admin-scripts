#!/bin/sh
#! perl, to stop looping
eval 'exec perl -x -Sw $0 ${1+"$@"}'
  if 0;

# open a mailspool file and remail each message to the email address given
# on the commandline

use strict;
use Mail::Internet;
use Mail::Header;

sub processMessage($);

my $filename = shift || die "Must specify a mailbox as the first argument";
my $to = shift || die "Must specify an email address to send all messages to as the second argument";

open INPUT, "<$filename" || die "Cannot open $filename: $!";
my $messageStart = 0;
my @lines = ();
my $line;
while ($line = <INPUT>) {
  if ($line =~ /^From /) {
    if ($messageStart) {
      #found a new message, previous one is now in @lines, better process it
      my $message = new Mail::Internet([@lines], Modify => 0);
      processMessage($message);
      @lines = ();
    } else {
      $messageStart = 1;
    }
  }
  push @lines, $line;
}
#process last message
my $message = new Mail::Internet([@lines], Modify => 0);
processMessage($message);
    
close INPUT;

sub processMessage($) {
  my $message = shift;

  my $header = $message->head();
  $header->delete('To');
  $header->delete('Cc');
  $header->delete('Bcc');
  $header->add('To', $to);

  #$message->print(\*STDOUT);
  
  my @sent = ();
  while (scalar @sent == 0) {
    @sent = $message->smtpsend(
                               Host => 'mtu.net',
                              );
    if (scalar @sent == 0) {
      print "Message not sent, sleeping for 10 seconds and trying again\n";
      sleep 10;
    }
  }

}
