

class OneHandSequenceExampleGenerator:
    def __init__(self, deal_records: List[DealRecord], features: List, deal_targets: List):
        self.deal_targets = deal_targets
        self.deal_records = deal_records
        self.features = features

    def __iter__(self):
        for deal_record in self.deal_records:
            dealer = deal_record.deal.dealer
            player_holdings = {dealer.offset(i): holding(dealer.offset(i), deal_record) for i in range(4)}
            # deal targets do not change with each sequence so can be cached
            calculated_deal_targets = {
                type(deal_target).__name__: deal_target.calculate(deal_record) for deal_target in self.deal_targets
            }
            for board_record in deal_record.board_records:
                #print(deal_record.deal, board_record)
                bidding_data = BiddingSequenceExampleData(deal_record, board_record, player_holdings)
                yield self.build_sequence_example(bidding_data, calculated_deal_targets)
                # bidding_sequences = self.generate_bidding_sequences(dealer, board_record)
                # for direction, bidding_sequence in bidding_sequences:
                #    example_data = BiddingExampleData(
                #        direction, bidding_sequence, deal_record, board_record, player_holdings
                #    )
                #    print(example_data)
                #    yield self.build_example(example_data, calculated_deal_targets)

    def build_sequence_example(self, bidding_data: BiddingSequenceExampleData, calculated_deal_targets: Dict):
        context = tf.train.Features(feature=calculated_deal_targets)
        feature_map = {type(feature).__name__: feature.calculate(bidding_data) for feature in self.features}
        '''
        feature_list_entries = [
            tf.train.FeatureLists.FeatureListEntry(key=type(feature).__name__, value=feature.calculate(bidding_data))
            for feature in self.features
        ]'''
        feature_lists = tf.train.FeatureLists(feature_list=feature_map)
        return tf.train.SequenceExample(context=context, feature_lists=feature_lists)