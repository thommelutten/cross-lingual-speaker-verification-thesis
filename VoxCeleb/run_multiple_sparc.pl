#!/usr/bin/perl
use warnings;
use File::Path;
use File::Copy;

$SPARC_tests_folder="SPARC_multiple";

open(LIST_OF_TESTS, "<$SPARC_tests_folder/enrollment_test_channel_combinations.tsv") or die "cannot open wav list";


my @tests = ();

while(<LIST_OF_TESTS>) {
  $line = $_;
  @toks = split(" ", $line);
  $enrollment = $toks[0];
  $test = $toks[1];
  $channel_enrollment = $toks[2];
  $channel_test = $toks[3];
  push @tests, "$enrollment-$test-$channel_enrollment-$channel_test";
}

open(RESULTS, ">results_SWAN.csv") || die "Could not open the output file results.csv";

my $test_counter = 1;
my $size_of_tests = scalar(@tests)-1;

$dirname ="score_files";

mkdir $dirname, 0755;

for (@tests[1 .. $#tests])
{
  $test = $_;
  @toks = split("-", $test);
  $enrollment = $toks[0];
  $test = $toks[1];
  $channel_enrollment = $toks[2];
  $channel_test = $toks[3];
  $test_to_run = "$enrollment-$test-$channel_enrollment-$channel_test";

  print "Test running: $test_to_run - Test number $test_counter out of $size_of_tests\n";
  $output = `/bin/bash run_SWAN.sh $test_to_run`;
  print($output);
  @output_split = split("\n", $output);
  # print($output_split);
  $result = $output_split[-1];
  print "$result\n";
  # @plda_results = split(",", $result);
  # $a_plda = $plda_results[0];
  # $ood_plda = $plda_results[1];


  print RESULTS "$enrollment, $test, $channel_enrollment, $channel_test $result \n";
  $scores_path = "exp/scores";
  copy("exp/scores_voxceleb1_test","$dirname/$test_to_run") or die "Copy failed: $!";
  $data_path = "data";
  $scores_path = "exp/scores";
  rmtree($data_path);
  rmtree($scores_path);
  $test_counter++;
}

close(RESULTS) || die;
