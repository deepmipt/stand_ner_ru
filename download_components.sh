#!/bin/bash
echo downloading model files..
wget http://lnsigo.mipt.ru/export/deepreply_data/stand_ner_ru/model.tar.gz &&
tar -zxvf model.tar.gz &&
rm model.tar.gz &&
echo download successful