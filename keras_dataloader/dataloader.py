from concurrent.futures import ThreadPoolExecutor

import keras
import numpy as np

from keras_dataloader.dataset import Dataset


def default_collate_fn(samples):
    X = np.array([sample[0] for sample in samples])
    Y = np.array([sample[1] for sample in samples])

    return X, Y


class DataGenerator(keras.utils.Sequence):

    def __init__(self,
                 dataset: Dataset,
                 collate_fn=default_collate_fn,
                 batch_size=32,
                 shuffle=True,
                 num_workers=0,
                 replacement: bool = False,
                 drop_last: bool = True,
                 ):
        """

        :param dataset (Dataset): Data set to load
        :param batch_size (int): how many samples in one batch
        :param shuffle (bool, optional): set to ``True`` to have the data reshuffled
            at every epoch (default: ``True``).
        :param num_workers (int, optional): how many threads to use for data
            loading in one batch. 0 means that the data will be loaded in the main process.
            (default: ``0``)
        :param replacement (bool): samples are drawn with replacement if ``True``, default=False
        :param drop_last (bool): uneven samples are ignored with drop_last if ``False``, default=False
        :param collate_fn (callable, optional):
        """
        self.dataset = dataset
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.replacement = replacement
        self.drop_last = drop_last
        self.indices = []
        self.collate_fn = collate_fn
        self.on_epoch_end()

    def __getitem__(self, index):
        indices = self.indices[index * self.batch_size: (index + 1) * self.batch_size]

        samples = []
        if self.num_workers == 0:
            for i in indices:
                data = self.dataset[i]
                samples.append(data)
        else:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                for sample in executor.map(lambda i: self.dataset[i], indices):
                    samples.append(sample)
        X, Y = self.collate_fn(samples)
        return X, Y

    def on_epoch_end(self):
        n = len(self.dataset)
        seq = np.arange(0, n)
        if self.shuffle:
            if self.replacement:
                self.indices = np.random.randint(low=0, high=n, size=(n,),
                                                 dtype=np.int64).tolist()
            else:
                np.random.shuffle(seq)
                self.indices = seq
        else:
            self.indices = seq

    def __len__(self):
        if self.drop_last:
            return int(np.floor(len(self.dataset) / self.batch_size))
        else:
            return int(np.ceil(len(self.dataset) / self.batch_size))
