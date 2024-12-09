import React, { useState } from "react";
import PropTypes from "prop-types";

import axios from "axios";
import { isEmpty } from "lodash-es";

import {
  Button,
  Col,
  Divider,
  Input,
  List,
  Row,
  Skeleton,
  Space,
} from "antd";
import CAPDeposit from "./services/CAPDeposit";
import { DeleteOutlined } from "@ant-design/icons";
import InfiniteScroll from "react-infinite-scroll-component";

// This component should always return an object with properties: url, data
// url: (required) URL pointing to the resource to fetch
// data: fetched data from the provided URL

const ImportDataField = ({ uiSchema, formData, onChange }) => {

  const [fetchedResults, setFetchedResults] = useState([]);
  const [fetchedResultsTotal, setFetchedResultsTotal] = useState(0);
  const [data, setData] = useState(formData?.data);

  const [searchValue, setSearchValue] = useState("");
  const [searchPage, setSearchPage] = useState(1);

  const {
    "x-cap-import-data": {
      queryUrl = "/api/deposits",
      // queryUrl = "",
      queryParam = "q",
      resultsPath = "hits.hits",
      resultsTotalPath = null,
      // resultsTotalPath = "hits.total",
      hitTitle = "metadata.general_title",
      hitDescription = "created_by.email",
      // hitLink = "links.self",
      // hitDataPath = ""
    } = {},
  } = uiSchema || {};

  const getResultFromData = data => {
    let results = data;
    const resultPathArray = resultsPath.split(".");
    resultPathArray.map(p => (results = results[p]));
    return results;
  };

  const getResultTotalFromData = data => {
    let resultsTotal = data;
    const resultTotalPathArray = resultsTotalPath.split(".");
    resultTotalPathArray.map(p => (resultsTotal = resultsTotal[p]));
    return resultsTotal;
  };

  // const getHitFromData = data => {
  //   let hit = data;
  //   const hitPathArray = hitDataPath.split(".");
  //   hitPathArray.map(p => (hit = hit[p]));
  //   return hit;
  // };

  const serializeResults = data => {
    return data.map(entry => {
      let title = entry;
      let description = entry;

      hitTitle.split(".").map(i => (title = title[i]));
      hitDescription.split(".").map(i => (description = description[i]));
      return {
        label: title,
        value: description,
        data: entry,
      };
    });
    // let results = data;
    // const resultPathArray = resultsPath.split(".");
    // resultPathArray.map(p => (results = results[p]));
    // return results;
  };

  const updateSearchValue = input => {
    clearSearch();
    if (!isEmpty(input?.target?.value)) {
      setSearchValue(input?.target?.value);
    }
  };

  const clearSearch = () => {
    setSearchValue("");
    setFetchedResults([]);
    setFetchedResultsTotal(0);
    setSearchPage(1);
  };

  const _onSearch = (value, event, { source = "input" } = {}) => {
    if (source == "input") {
      fetchSuggestions();
    }
  };
  const fetchSuggestions = async (fetchNext = false) => {
    let newSearchPage = searchPage;
    if (fetchNext) {
      newSearchPage = searchPage + 1;
      setSearchPage(newSearchPage);
    }
    // try {
      const { data } = await axios.get(queryUrl, {
        params: {
          [queryParam]: searchValue,
          page: searchPage,
        },
      });

      if (!isEmpty(resultsTotalPath)) {
        let totalResults = getResultTotalFromData(data);
        setFetchedResultsTotal(totalResults);
      }
      let results = getResultFromData(data);
      results = serializeResults(results);
      setFetchedResults([...fetchedResults, ...results]);
    // } catch (err) {
    //   //
    // }
  };

  if (data) {
    return (
      <Row wrap={false} align="middle" gutter={10}>
        <Col flex="auto">
          <CAPDeposit data={data} />
        </Col>
        <Col flex="none">
          <Button
            size="small"
            danger
            onClick={() => {
                  onChange(null)
                  setData(null);
                  setFetchedResults([]);
                }}
            icon={<DeleteOutlined />}
          />
        </Col>
      </Row>
    );
  }
  return (
    <Space direction="vertical" style={{ flex: 1, display: "flex" }}>
      <Input.Search
        enterBdutton="Fetch"
        placeholder="Insert your pattern e.x /dataset/*"
        allowClear
        value={searchValue}
        cle
        onChange={updateSearchValue}
        onSearch={_onSearch}
      />
      {!isEmpty(fetchedResults) && (
        <InfiniteScroll
          dataLength={fetchedResults.length}
          height={"200px"}
          next={() => fetchSuggestions(true)}
          hasMore={fetchedResults.length < fetchedResultsTotal}
          style={{ backgroundColor: "#fff" }}
          loader={
            <List size="small">
              <List.Item>
                <Skeleton
                  paragraph={{ rows: 1 }}
                  active
                  style={{ height: "10px" }}
                />
              </List.Item>
            </List>
          }
          endMessage={<Divider plain>It is all, nothing more 🤐</Divider>}
        >
          <List
            dataSource={fetchedResults}
            borderedd
            size="small"
            style={{ backgroundColor: "#fff" }}
            renderItem={item => (
              <List.Item
                key={item.value}
                onClick={() => {
                  onChange({
                    url: item?.data?.links?.self,
                    data: item.data
                  })
                  setData(item.data);
                  setFetchedResults([]);
                }}
              >
                <List.Item.Meta
                  title={item.label}
                  // avatar={<Avatar style={{ background: "#10899e" }} />}
                  description={item.value}
                />
              </List.Item>
            )}
          />
        </InfiniteScroll>
      )}
    </Space>
  );
};

ImportDataField.propTypes = {
  onChange: PropTypes.func,
  uiSchema: PropTypes.object,
  formData: PropTypes.object,
};

export default ImportDataField;
