import React from 'react'
import { Card, Row, Col, Statistic, Tag } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'

const MarketOverview = ({ data }) => {
  if (!data) return null

  const { btc_price, eth_price, btc_change_24h, eth_change_24h } = data

  return (
    <Card title="市场概览" bordered={false}>
      <Row gutter={16}>
        <Col span={12}>
          <Statistic
            title="Bitcoin (BTC)"
            value={btc_price}
            precision={2}
            prefix="$"
            valueStyle={{ color: btc_change_24h >= 0 ? '#3f8600' : '#cf1322' }}
            suffix={
              <Tag color={btc_change_24h >= 0 ? 'green' : 'red'}>
                {btc_change_24h >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                {Math.abs(btc_change_24h).toFixed(2)}%
              </Tag>
            }
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Ethereum (ETH)"
            value={eth_price}
            precision={2}
            prefix="$"
            valueStyle={{ color: eth_change_24h >= 0 ? '#3f8600' : '#cf1322' }}
            suffix={
              <Tag color={eth_change_24h >= 0 ? 'green' : 'red'}>
                {eth_change_24h >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                {Math.abs(eth_change_24h).toFixed(2)}%
              </Tag>
            }
          />
        </Col>
      </Row>
    </Card>
  )
}

export default MarketOverview
