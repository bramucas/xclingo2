TEST_DIR=/home/velka/projs/asp/xclingo2/proj/tests/test_xclingo
TEST_SUFFIX=_test.lp
RESULT_SUFFIX=_res.pickle


python -m xclingo -n 0 0 $TEST_DIR/_annotation_operator$TEST_SUFFIX \
    --picklefile $TEST_DIR/_annotation_operator$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/_cond_lit$TEST_SUFFIX \
    --picklefile $TEST_DIR/_cond_lit$RESULT_SUFFIX \
    --auto-tracing=all

python -m xclingo -n 0 0 $TEST_DIR/_ignore_non_labelled_constraints$TEST_SUFFIX \
    --picklefile $TEST_DIR/_ignore_non_labelled_constraints$RESULT_SUFFIX \
    --auto-tracing=all

python -m xclingo -n 0 0 $TEST_DIR/_mute_body$TEST_SUFFIX \
    --picklefile $TEST_DIR/_mute_body$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/_showtrace_1$TEST_SUFFIX \
    --picklefile $TEST_DIR/_showtrace_1$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/_showtrace_2$TEST_SUFFIX \
    --picklefile $TEST_DIR/_showtrace_2$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/_showtrace_3$TEST_SUFFIX \
    --picklefile $TEST_DIR/_showtrace_3$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/_trace_1$TEST_SUFFIX \
    --picklefile $TEST_DIR/_trace_1$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/_trace_2$TEST_SUFFIX \
    --picklefile $TEST_DIR/_trace_2$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/_trace_3$TEST_SUFFIX \
    --picklefile $TEST_DIR/_trace_3$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/4graphs$TEST_SUFFIX \
    --picklefile $TEST_DIR/4graphs$RESULT_SUFFIX \
    --auto-tracing=all

python -m xclingo -n 0 0 $TEST_DIR/constraint1$TEST_SUFFIX \
    --picklefile $TEST_DIR/constraint1$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/count_aggregate$TEST_SUFFIX \
    --picklefile $TEST_DIR/count_aggregate$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/diag$TEST_SUFFIX \
    --picklefile $TEST_DIR/diag$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/diamond_with_mute$TEST_SUFFIX \
    --picklefile $TEST_DIR/diamond_with_mute$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/disyunction$TEST_SUFFIX \
    --picklefile $TEST_DIR/disyunction$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/dont_drive_drunk$TEST_SUFFIX \
    --picklefile $TEST_DIR/dont_drive_drunk$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/happy$TEST_SUFFIX \
    --picklefile $TEST_DIR/happy$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/ignore_shows$TEST_SUFFIX \
    --picklefile $TEST_DIR/ignore_shows$RESULT_SUFFIX \
    --auto-tracing=all

python -m xclingo -n 0 0 $TEST_DIR/obligations_gentle_killer$TEST_SUFFIX \
    --picklefile $TEST_DIR/obligations_gentle_killer$RESULT_SUFFIX \

python -m xclingo -n 0 0 $TEST_DIR/pool_and_choice$TEST_SUFFIX \
    --picklefile $TEST_DIR/pool_and_choice$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/pool_and_choice2$TEST_SUFFIX \
    --picklefile $TEST_DIR/pool_and_choice2$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/single_strongneg$TEST_SUFFIX \
    --picklefile $TEST_DIR/single_strongneg$RESULT_SUFFIX

python -m xclingo -n 0 0 $TEST_DIR/unbalanced_table$TEST_SUFFIX \
    --picklefile $TEST_DIR/unbalanced_table$RESULT_SUFFIX \
    --auto-tracing=all

python -m xclingo -n 0 0 $TEST_DIR/_unary_operator$TEST_SUFFIX \
    --picklefile $TEST_DIR/_unary_operator$RESULT_SUFFIX \
    --auto-tracing=all
